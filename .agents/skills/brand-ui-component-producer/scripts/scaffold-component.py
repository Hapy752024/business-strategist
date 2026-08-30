#!/usr/bin/env python3
"""Scaffold a Next.js/React component folder with Component.tsx, .test.tsx, .stories.tsx.

Usage:
  scaffold-component.py --name <PascalName> --tier <core|extended|domains/<pack>> --base <shadcn-primitive> --output-dir <components-dir>

The folder is created at <output-dir>/<tier>/<kebab-name>/.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def pascal_to_kebab(name: str) -> str:
    out = []
    for i, c in enumerate(name):
        if c.isupper() and i > 0:
            out.append("-")
        out.append(c.lower())
    return "".join(out)


COMPONENT_TEMPLATE = '''"use client";

import * as React from "react";
import {{ cn }} from "@/lib/utils";

export interface {name}Props extends React.HTMLAttributes<HTMLDivElement> {{
  className?: string;
}}

export const {name} = React.forwardRef<HTMLDivElement, {name}Props>(
  ({{ className, ...props }}, ref) => (
    <div
      ref={{ref}}
      className={{cn(
        "rounded-[var(--radius-md)] bg-[var(--color-background)] text-[var(--color-foreground)]",
        "transition-[box-shadow,transform] duration-[var(--motion-duration-responsive-default)] ease-[var(--motion-ease-responsive-standard)]",
        className
      )}}
      {{...props}}
    />
  )
);
{name}.displayName = "{name}";
'''

TEST_TEMPLATE = '''import {{ describe, it, expect }} from "vitest";
import {{ render, screen }} from "@testing-library/react";
import axe from "jest-axe";
import {{ {name} }} from "./{name}";

describe("{name}", () => {{
  it("renders without crashing", () => {{
    render(<{name} data-testid="subject">Hello</{name}>);
    expect(screen.getByTestId("subject")).toBeDefined();
  }});

  it("has no critical a11y violations", async () => {{
    const {{ container }} = render(<{name}>Hello</{name}>);
    const results = await axe(container);
    expect(results.violations.filter(v => v.impact === "critical")).toHaveLength(0);
  }});

  it("references at least one brand or motion token", () => {{
    const {{ container }} = render(<{name}>Hello</{name}>);
    const html = container.innerHTML;
    expect(html).toMatch(/var\\(--(color|motion)-/);
  }});
}});
'''

STORIES_TEMPLATE = '''import type {{ Meta, StoryObj }} from "@storybook/react";
import {{ {name} }} from "./{name}";

const meta: Meta<typeof {name}> = {{
  title: "Components/{name}",
  component: {name},
  parameters: {{ layout: "centered" }},
}};

export default meta;
type Story = StoryObj<typeof {name}>;

export const Default: Story = {{
  args: {{ children: "Default" }},
}};

export const Hover: Story = {{
  args: {{ children: "Hover", className: "hover:shadow-lg" }},
}};
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="PascalCase component name")
    parser.add_argument("--tier", required=True, help="core | extended | domains/<pack>")
    parser.add_argument("--base", required=True, help="shadcn primitive name (kebab-case)")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)

    kebab = pascal_to_kebab(args.name)
    folder = args.output_dir / args.tier / kebab
    folder.mkdir(parents=True, exist_ok=True)

    (folder / f"{args.name}.tsx").write_text(
        COMPONENT_TEMPLATE.format(name=args.name, base=args.base)
    )
    (folder / f"{args.name}.test.tsx").write_text(
        TEST_TEMPLATE.format(name=args.name)
    )
    (folder / f"{args.name}.stories.tsx").write_text(
        STORIES_TEMPLATE.format(name=args.name)
    )

    print(f"Scaffolded {args.name} at {folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
