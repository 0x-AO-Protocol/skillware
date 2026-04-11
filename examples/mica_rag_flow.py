import os
import json
import re
import google.generativeai as genai
from skillware.core.loader import SkillLoader
from skillware.core.env import load_env_file


def main():
    # 1. Setup
    load_env_file()
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

    print("[System] Loading MiCA Module (Cognitive/Surgical Mode)...")
    skill_bundle = SkillLoader.load_skill("compliance/mica_module")
    # Instantiate the logic
    MiCA_Module = skill_bundle["module"].MiCAModuleSkill
    mica_skill = MiCA_Module()

    # 2. Build the "Cognitive Map" (System Instructions + Manifest)
    # We use the un-altered manifest name here (slashes are fine in text prompts!)
    tool_text = SkillLoader.to_ollama_prompt(skill_bundle)

    system_instruction = f"""{skill_bundle.get('instructions', '')}

**Available Tools in your Mind:**
{tool_text}

**Protocol:**
If you need regulatory context, output a JSON block like this:
```json
{{
  "tool": "{skill_bundle['manifest']['name']}",
  "arguments": {{ "user_prompt": "query" }}
}}
```
Wait for the response before making your final compliant determination.
"""

    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    user_query = "How do I get an authorization to be a crypto-asset service provider (CASP) in the EU?"

    print(f"\n[User]: {user_query}")
    print("-" * 50)

    chat = model.start_chat()
    result_msg = ""

    print("Agent (Gemini) is thinking...", flush=True)

    # turn limit for safety
    for turn in range(3):
        try:
            # First turn uses the prompt, subsequent turns use the skill result
            prompt = (
                system_instruction + "\n\nUSER QUERY: " + user_query
                if turn == 0
                else result_msg
            )

            # Use streaming for visual feedback
            response = chat.send_message(prompt, stream=True)

            full_content = ""
            print("\n[Agent]: ", end="", flush=True)
            for chunk in response:
                print(chunk.text, end="", flush=True)
                full_content += chunk.text

            # Extract Tool Call
            match = re.search(r"```json\s*({.*?})\s*```", full_content, re.DOTALL)
            if match:
                call_data = json.loads(match.group(1))
                fn_args = call_data.get("arguments", {})

                print(
                    "\n\n[Skillware] Match Detected. Executing Surgical RAG...",
                    end="",
                    flush=True,
                )
                result = mica_skill.execute(fn_args)
                print(" [DONE]")

                sections = result.get("retrieved_sections", [])
                print(f" > Articles found: {', '.join(sections)}")

                # Feedback loop
                result_msg = (
                    f"SYSTEM RESPONSE (Source Articles):\n{result.get('final_context_for_agent', '')}\n\n"
                    "Please generate your final authorized response."
                )
            else:
                # No more tool calls, done
                print("\n\n(Scenario Complete)")
                break

        except Exception as e:
            print(f"\n[Error]: {e}")
            break


if __name__ == "__main__":
    main()
