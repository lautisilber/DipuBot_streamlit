"""Prueba visual reproducible contra tests/ui_fixture.py en el puerto 8517."""
from playwright.sync_api import sync_playwright


def check(browser_type):
    browser = browser_type.launch()
    try:
        for width, height in [(320, 640), (390, 844), (430, 932), (768, 1024), (1280, 900)]:
            page = browser.new_page(viewport={"width": width, "height": height},
                                    is_mobile=width < 768, device_scale_factor=1)
            page.goto("http://localhost:8517")
            field = page.locator('[data-testid="stChatInput"] textarea')
            field.wait_for(timeout=60000)
            page.wait_for_timeout(600)
            sidebar = page.locator('[data-testid="stSidebar"]')
            if sidebar.get_attribute("aria-expanded") == "true":
                page.locator('[data-testid="stSidebarCollapseButton"] button').click()
                page.wait_for_timeout(400)
            assert not sidebar.is_visible(), (browser_type.name, width, "closed sidebar visible")
            box = page.locator('[data-testid="stChatInput"]').bounding_box()
            if width <= 640:
                assert height - box["y"] - box["height"] < 35, (browser_type.name, width, box)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "horizontal overflow"
            field.focus()
            page.set_viewport_size({"width": width, "height": max(360, height - 300)})
            page.wait_for_timeout(400)
            assert field.is_visible()
            if width <= 640:
                box = page.locator('[data-testid="stChatInput"]').bounding_box()
                assert max(360, height - 300) - box["y"] - box["height"] < 35
            page.set_viewport_size({"width": width, "height": height})
            page.locator('[data-testid="stExpandSidebarButton"]').click()
            page.wait_for_timeout(400)
            assert sidebar.is_visible()
            page.get_by_role("link", name="¿Qué es DipuBot?", exact=True).click()
            page.get_by_role("heading", name="¿Qué es DipuBot?", exact=True).wait_for()
            assert "únicamente" in page.locator('[data-testid="stMain"]').inner_text()
            assert "├" not in page.locator('[data-testid="stMain"]').inner_text()
            if sidebar.get_attribute("aria-expanded") != "true":
                page.locator('[data-testid="stExpandSidebarButton"]').click()
            page.get_by_role("link", name="¿Cómo funciona el Congreso?", exact=True).click()
            page.get_by_role("heading", name="¿Cómo funciona el poder legislativo?", exact=True).wait_for()
            assert "├" not in page.locator('[data-testid="stMain"]').inner_text()
            print(browser_type.name, width, "OK", flush=True)
            page.close()
    finally:
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        check(playwright.chromium)
        check(playwright.webkit)
