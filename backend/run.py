#!/usr/bin/env python
"""Convenience entry-point: python run.py"""
import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    s = get_settings()
    uvicorn.run("app.main:app", host=s.HOST, port=s.PORT, reload=True)
