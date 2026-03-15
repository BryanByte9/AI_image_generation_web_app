from flask import Blueprint, render_template, current_app

main_bp = Blueprint("main", __name__)

@main_bp.get("/")
def home():
    return render_template(
        "index.html",
        max_prompt_len=current_app.config.get("MAX_PROMPT_LEN", 500),
    )
