import fitz  # PyMuPDF
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

class FieldType(Enum):
    TEXT = "text"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    RADIO = "radio"

@dataclass
class DetectedField:
    """Represents a detected form field in the PDF."""
    field_id: str
    field_type: FieldType
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    page: int
    label_context: str  # nearby text for semantic understanding
    current_value: Optional[str] = None
    options: Optional[List[str]] = None
    native_field_name: Optional[str] = None
    friendly_label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['field_type'] = self.field_type.value
        return d

def _widget_type_to_field_type(widget_type: int) -> FieldType:
    mapping = {
        7: FieldType.TEXT,         # PDF_WIDGET_TYPE_TEXT
        2: FieldType.CHECKBOX,     # PDF_WIDGET_TYPE_CHECKBOX
        3: FieldType.DROPDOWN,     # PDF_WIDGET_TYPE_COMBOBOX
        4: FieldType.DROPDOWN,     # PDF_WIDGET_TYPE_LISTBOX
        5: FieldType.RADIO,        # PDF_WIDGET_TYPE_RADIOBUTTON
    }
    return mapping.get(widget_type, FieldType.TEXT)

def _extract_nearby_text(page: "fitz.Page", rect: "fitz.Rect", radius: int = 100) -> str:
    """Extract text near a bounding box to understand field context."""
    search_rect = fitz.Rect(rect)
    search_rect.x0 -= radius
    search_rect.y0 -= radius
    search_rect.x1 += radius
    search_rect.y1 += radius
    
    # Clip to page bounds
    page_rect = page.rect
    search_rect.intersect(page_rect)
    
    text = page.get_text("text", clip=search_rect).strip()
    
    # Clean up whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return ' | '.join(lines)

def detect_form_fields(pdf_bytes: bytes) -> List[DetectedField]:
    """Detect all fillable AcroForm fields in the PDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    fields = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # PyMuPDF 1.22+ uses page.widgets(), older versions use page.load_widgets() or similar
        # Assuming modern PyMuPDF based on target repo
        for widget in page.widgets():
            if not widget.field_name:
                continue
                
            field_type = _widget_type_to_field_type(widget.field_type)
            
            options = None
            # Using integer constants to avoid linter errors
            # 3 = COMBOBOX, 4 = LISTBOX
            if widget.field_type in (3, 4):
                # Retrieve options for dropdown/listbox
                # widget.choice_values is sometimes available
                if hasattr(widget, "choice_values"):
                    options = list(widget.choice_values) or []
                
            current_value = widget.field_value
            if isinstance(current_value, bool):
                current_value = str(current_value).lower()
            
            # Context extraction
            label = _extract_nearby_text(page, widget.rect)
                
            fields.append(DetectedField(
                field_id=f"page{page_num}_{widget.field_name}",
                field_type=field_type,
                bbox=tuple(widget.rect),
                page=page_num,
                label_context=label,
                current_value=str(current_value) if current_value is not None else None,
                options=options,
                native_field_name=widget.field_name
            ))
            
    doc.close()
    return fields

# Define FieldEdit dataclass for type hinting
@dataclass
class FieldEdit:
    field_id: str
    value: Any

def apply_edits(pdf_bytes: bytes, edits: list[FieldEdit]) -> bytes:
    """Apply edits to the PDF based on field_id -> value mapping."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    edit_map = {e.field_id: e for e in edits}
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        for widget in page.widgets():
            if not widget.field_name:
                continue
                
            field_id = f"page{page_num}_{widget.field_name}"
            
            if field_id in edit_map:
                edit = edit_map[field_id]
                _apply_widget_edit(widget, edit.value)
                
    result = doc.tobytes()
    doc.close()
    return result

def _apply_widget_edit(widget: "fitz.Widget", value: Any):
    """Helper to apply value to a specific widget."""
    # Checkbox logic: 2 = CHECKBOX
    if widget.field_type == 2:
        # PyMuPDF expects boolean for checkbox state
        if isinstance(value, str):
            value = value.lower() in ('true', 'yes', '1', 'on', 'checked')
        widget.field_value = bool(value)
    else:
        # Text/Choice logic
        widget.field_value = str(value)
    
    # Update appearance
    widget.update()
