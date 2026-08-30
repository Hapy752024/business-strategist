#!/usr/bin/env node
import { readFileSync } from "node:fs";

const path = process.argv[2];
if (!path) throw new Error("usage: validate-experiment.mjs <experiment.json>");
const experiment = JSON.parse(readFileSync(path, "utf8"));
const required = ["hypothesis", "changed_variable", "primary_metric", "control", "treatment", "allocation", "stop_rule"];
const errors = required.filter((key) => !experiment[key]).map((key) => `missing ${key}`);
if (experiment.control === experiment.treatment) errors.push("control and treatment must differ");
if (experiment.changed_variables && experiment.changed_variables.length !== 1) errors.push("exactly one changed variable is allowed");
if (experiment.contains_pii) errors.push("experiment telemetry may not contain PII");
const result = { status: errors.length ? "fail" : "pass", errors };
console.log(JSON.stringify(result, null, 2));
process.exitCode = errors.length ? 1 : 0;
