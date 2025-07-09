from django.core.exceptions import ValidationError

def validate_jd_length(value):
    min_length = 50
    max_length = 10000
    if len(value) < min_length:
        raise ValidationError(
            f"Job description too short (min {min_length} chars)"
        )
    if len(value) > max_length:
        raise ValidationError(
            f"Job description too long (max {max_length} chars)"
        )