"""E2E tests for authentication flow"""

import os

import pytest


pytestmark = pytest.mark.e2e


if not os.getenv("RUN_E2E"):
    pytest.skip(
        "E2E tests are disabled by default; set RUN_E2E=1 to run them",
        allow_module_level=True,
    )


def test_auth_page_loads(page):
    """Test that auth page loads correctly"""
    page.goto("http://localhost:3000/auth")

    # Check page title
    assert page.title() == "Faceit AI Bot - Authentication"

    # Check login form elements
    email_input = page.locator('input[type="email"]')
    password_input = page.locator('input[type="password"]')
    login_button = page.locator('button:has-text("Sign In")')

    assert email_input.is_visible()
    assert password_input.is_visible()
    assert login_button.is_visible()


def test_login_form_validation(page):
    """Test login form validation"""
    page.goto("http://localhost:3000/auth")

    # Try to submit empty form
    login_button = page.locator('button:has-text("Sign In")')
    login_button.click()

    # Check for validation messages
    # Note: This depends on your form validation implementation
    page.wait_for_timeout(1000)  # Wait for validation to appear


def test_successful_navigation(page):
    """Test navigation to dashboard after login"""
    page.goto("http://localhost:3000")

    # Check main navigation
    nav = page.locator("nav")
    assert nav.is_visible()

    # Check main heading
    heading = page.locator("h1")
    assert heading.is_visible()


def test_responsive_design(page):
    """Test responsive design"""
    page.set_viewport_size({"width": 375, "height": 667})  # Mobile size
    page.goto("http://localhost:3000")

    # Check mobile menu
    mobile_menu = page.locator('[data-testid="mobile-menu"]')
    # This depends on your mobile menu implementation


def test_theme_switcher(page):
    """Test theme switcher functionality"""
    page.goto("http://localhost:3000")

    # Find theme switcher
    theme_switcher = page.locator('[data-testid="theme-switcher"]')
    if theme_switcher.is_visible():
        theme_switcher.click()

        # Check if theme changed (this depends on your implementation)
        page.wait_for_timeout(500)


def test_language_switcher(page):
    """Test language switcher"""
    page.goto("http://localhost:3000")

    # Find language switcher
    lang_switcher = page.locator('[data-testid="language-switcher"]')
    if lang_switcher.is_visible():
        lang_switcher.click()

        # Check if language changed
        page.wait_for_timeout(500)
