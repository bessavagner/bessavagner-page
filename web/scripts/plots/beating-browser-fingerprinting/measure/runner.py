"""Measure 3 configs against: transparent automation-tells panel, BotD, CreepJS lies.

Configs:
  vanilla  - stock Selenium Chrome
  stealth  - selenium-stealth patches (webdriver, languages, vendor, webgl, UA)
  uc       - undetected-chromedriver

Outputs results/results.json with NUMBERS ONLY (no IPs / fingerprints).
"""
import json, time, pathlib, traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

BOTD = "http://localhost:8901/botd.html"
TELLS = "http://localhost:8901/tells.html"
CREEP = "http://localhost:8902/"
OUT = pathlib.Path(__file__).parent / "results" / "results.json"


def base_options():
    o = Options()
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    o.add_argument("--window-size=1280,900")
    return o


def make_vanilla():
    return webdriver.Chrome(options=base_options())


def make_stealth():
    o = base_options()
    o.add_argument("--disable-blink-features=AutomationControlled")
    o.add_experimental_option("excludeSwitches", ["enable-automation"])
    d = webdriver.Chrome(options=o)
    from selenium_stealth import stealth
    stealth(d, languages=["en-US", "en"], vendor="Google Inc.",
            platform="Win32", webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    return d


def make_uc():
    import undetected_chromedriver as uc
    o = uc.ChromeOptions()
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    o.add_argument("--window-size=1280,900")
    # Pin to the installed Chrome (149); uc otherwise grabs the latest driver.
    return uc.Chrome(options=o, use_subprocess=True, version_main=149)


def run_tells(d):
    d.get(TELLS)
    WebDriverWait(d, 25).until(lambda x: x.execute_script("return window.__TELLS__ !== undefined"))
    return d.execute_script("return window.__TELLS__")


def run_botd(d):
    d.get(BOTD)
    WebDriverWait(d, 25).until(lambda x: x.execute_script("return window.__BOTD__ !== undefined"))
    r = d.execute_script("return window.__BOTD__")
    return r.get("result", r)


def run_creep_lies(d):
    d.get(CREEP)
    # CreepJS computes lies locally (its 'trust score' needs its API, which a
    # self-hosted copy can't reach). Wait for the FP ID to confirm it finished,
    # then count the rendered '.lies' (lied) badges = inconsistencies detected.
    ready = False
    for _ in range(45):
        time.sleep(1)
        info = d.execute_script(r"""
          const t = document.body.innerText || "";
          return { fpReady: /FP ID:\s*[0-9a-f]{16,}/i.test(t),
                   liedBadges: document.querySelectorAll('.lies').length };
        """)
        if info["fpReady"]:
            ready = True
            time.sleep(3)  # let any late lie rows render
            info = d.execute_script("return { liedBadges: document.querySelectorAll('.lies').length }")
            break
    info["ready"] = ready
    return info


CONFIGS = [("vanilla", make_vanilla), ("stealth", make_stealth), ("uc", make_uc)]


def measure_once():
    out = {}
    for name, factory in CONFIGS:
        print(f"  -- {name}", flush=True)
        entry = {}
        d = None
        try:
            d = factory()
            entry["tells"] = run_tells(d)
            entry["botd"] = run_botd(d)
            entry["creep"] = run_creep_lies(d)
            print(f"     tells {entry['tells']['passed']}/{entry['tells']['total']}"
                  f" | botd {entry['botd']} | creep_lies {entry['creep'].get('liedBadges')}", flush=True)
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {e}"
            print("     ERROR:", entry["error"], flush=True)
        finally:
            if d:
                try: d.quit()
                except Exception: pass
        out[name] = entry
    return out


if __name__ == "__main__":
    import sys
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    runs = []
    for i in range(trials):
        print(f"\n=== trial {i+1}/{trials} ===", flush=True)
        runs.append(measure_once())
    OUT.write_text(json.dumps(runs, indent=2))
    print("\nWROTE", OUT)
