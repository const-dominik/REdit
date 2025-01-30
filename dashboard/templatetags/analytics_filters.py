from django import template
from statistics import mean
import numpy as np

register = template.Library()


@register.filter
def sum_by_field(data, field):
    """Sum a field in the NumPy structured array."""
    try:
        return int(np.sum(data[field]))
    except Exception:
        return 0


@register.filter
def pluck_field(data, field):
    """Extract a field from the NumPy structured array as a list."""
    try:
        return list(data[field])
    except Exception:
        return []


@register.filter
def net_subscribers(data, fields):
    """Calculate net subscribers gained/lost."""
    try:
        field1, field2 = fields.split(",")
        gained = int(np.sum(data[field1]))  # Sum of field1
        lost = int(np.sum(data[field2]))  # Sum of field2
        return gained - lost  # Return the net value
    except Exception:
        return 0


@register.filter
def total_engagement(data, fields):
    """Calculate total engagement by summing specified fields (likes, comments, shares) over time."""
    try:
        field_list = fields.split(",")
        engagement_data = []

        field_indices = {
            "likes": 3,
            "comments": 2,
            "shares": 5,
        }

        for item in data:
            total = 0
            for field in field_list:
                if field in field_indices:
                    index = field_indices[field]
                    total += max(int(item[index]), 0)

            engagement_data.append(total)

        return engagement_data
    except Exception as e:
        print(f"Error in total_engagement filter: {e}")
        return []


@register.filter
def average(data, field):
    "Caluclate average"
    try:
        return float("{:.2f}".format(mean(data[field])))
    except Exception:
        return 0
