def create_card(title, content):
    """Creates a styled card with title and content"""
    return f"""
        <div class="stCard" style="margin-bottom: 1rem;">
            <h3 style="color: #0066cc !important; margin-bottom: 1rem;">{title}</h3>
            {content}
        </div>
    """