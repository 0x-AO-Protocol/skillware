import os
import sys

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import google.generativeai as genai  # noqa: E402
from skillware.core.loader import SkillLoader  # noqa: E402
from skillware.core.env import load_env_file  # noqa: E402

# Load Env (Requires GOOGLE_API_KEY for the Agent, and ANTHROPIC_API_KEY for the Skill's internal logic)
load_env_file()

# 1. Load the Skill
skill_bundle = SkillLoader.load_skill("office/pdf_form_filler")
print(f"Loaded Skill: {skill_bundle['manifest']['name']}")

# 2. Instantiate the Skill
# The skill needs ANTHROPIC_API_KEY in env to perform semantic mapping
PDFFormFillerSkill = skill_bundle["module"].PDFFormFillerSkill
pdf_skill = PDFFormFillerSkill()

# 3. Setup Gemini Agent
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Define tool for Gemini
tools = [SkillLoader.to_gemini_tool(skill_bundle)]

model = genai.GenerativeModel(
    "gemini-2.0-flash-exp",
    tools=tools,
    system_instruction=skill_bundle["instructions"],  # Inject skill's cognitive map
)

chat = model.start_chat(enable_automatic_function_calling=True)

# 4. Run the Agent Loop
# Note: You need a real PDF file for this to work.
pdf_path = os.path.abspath("test_form.pdf")
user_query = f"Fill out the form at {pdf_path}. Set the name to 'Jane Doe' and check the 'Subscribe' box."

print(f"User: {user_query}")

# Create a function map for manual execution if needed (Python SDK handles this automatically usually)
# But for completeness:
function_map = {"pdf_form_filler": pdf_skill.execute}

response = chat.send_message(user_query)

# Simple manual tool execution loop (if auto-calling isn't fully handled or we want to inspect)
# Note: Recent genai SDKs handle this better, but explicit loops are safer for demos.
while response.candidates and response.candidates[0].content.parts:
    part = response.candidates[0].content.parts[0]

    if part.function_call:
        fn_name = part.function_call.name
        fn_args = dict(part.function_call.args)

        print(f"🤖 Agent wants to call: {fn_name}")
        print(f"   Args: {fn_args}")

        if fn_name == "pdf_form_filler":
            try:
                # Check if file exists before running
                if not os.path.exists(fn_args.get("pdf_path", "")):
                    print(f"⚠️ Error: PDF file not found at {fn_args.get('pdf_path')}")
                    result = {"error": "PDF file not found."}
                else:
                    print("⚙️ Executing skill...")
                    result = pdf_skill.execute(fn_args)
                    print(f"✅ Result: {result}")
            except Exception as e:
                result = {"error": str(e)}

            # Send result back
            response = chat.send_message(
                [
                    {
                        "function_response": {
                            "name": fn_name,
                            "response": {"result": result},
                        }
                    }
                ]
            )
        else:
            break
    else:
        break

print("\n💬 Agent Final Response:")
print(response.text)
