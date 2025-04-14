/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { defineConfig } from "tsup";

export default defineConfig([
  {
    entry: ["src/index.ts"],
    format: ["cjs", "esm", 'iife'], // CommonJS and ES Modules
    dts: true, // Generate declaration files
    splitting: false,
    sourcemap: true,
    clean: true,
    minify: true,
    globalName: "secgeminisdk",
    outDir: "dist/",
    platform: 'browser',
    external: ['events'],
    esbuildOptions(options) {
      options.platform = 'browser'
      options.define = {
        ...options.define,
        'global': 'window'
      }
    },
  },
  {
    entry: {"secgeminisdk": "src/demo.ts"},
    format: ["cjs"],
    splitting: false,
    sourcemap: true,
    minify: false,
    outDir: "demo/",
  }
]);
