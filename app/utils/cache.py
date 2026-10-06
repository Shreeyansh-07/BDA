import streamlit as st
from functools import wraps

def cached_data(ttl=3600):
    """Decorator wrapping Streamlit cache_data with safe fallback."""
    def decorator(func):
        try:
            return st.cache_data(ttl=ttl, show_spinner=False)(func)
        except Exception:
            return func
    return decorator

def cached_resource():
    """Decorator wrapping Streamlit cache_resource with safe fallback."""
    def decorator(func):
        try:
            return st.cache_resource(show_spinner=False)(func)
        except Exception:
            return func
    return decorator
