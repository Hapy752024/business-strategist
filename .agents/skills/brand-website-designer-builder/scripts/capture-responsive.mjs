#!/usr/bin/env node
const url = process.argv[2] || "http://localhost:3000";
const viewports = [[375, 812], [390, 844], [768, 1024], [1440, 900]];
console.log(JSON.stringify({ url, viewports, command: "npx playwright screenshot --device=Desktop Chrome <url> <path>" }, null, 2));
