from datetime import datetime

def time_ago(dt):
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds > 60 * 60 * 24 * 365:
        years = int(seconds // (60 * 60 * 24 * 365))
        return f"{years} year{'s' if years > 1 else ''} ago"
    if seconds > 60 * 60 * 24 * 30:
        months = int(seconds // (60 * 60 * 24 * 30))
        return f"{months} month{'s' if months > 1 else ''} ago"
    if seconds > 60 * 60 * 24:
        days = int(seconds // (60 * 60 * 24))
        return f"{days} day{'s' if days > 1 else ''} ago"
    if seconds > 60 * 60:
        hours = int(seconds // (60 * 60))
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    if seconds > 60:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    return "just now"