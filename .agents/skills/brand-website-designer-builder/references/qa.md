# QA gate

Check 375x812, 390x844, 768x1024, and 1440x900; keyboard/focus/contrast/landmarks; reduced motion; loading/empty/success/validation/provider-error/retry states; missing assets and links; secret leakage; media/font layout stability; Core Web Vitals budgets; and the anti-template review. Require an independent brand-quality review and human approval of the actual Preview URL.

Run `python3 scripts/brand/validate_untrusted_asset.py <asset>` for imported SVG/HTML previews. Reject scripts, event handlers, unsafe `foreignObject`, executable URLs, and external resource loads before packaging.
