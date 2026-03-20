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

// List of cybersecurity-related terms
// prettier-ignore
const terms = [
  "firewall", "xss", "sql-injection", "csrf", "dos", "botnet", "rsa",
  "aes", "sha", "hmac", "xtea", "twofish", "serpent", "dh", "ecc",
  "dsa", "pgp", "vpn", "tor", "dns", "tls", "ssl", "https", "ssh",
  "sftp", "snmp", "ldap", "kerberos", "oauth", "bcrypt", "scrypt",
  "argon2", "pbkdf2", "ransomware", "trojan", "rootkit", "keylogger",
  "adware", "spyware", "worm", "virus", "antivirus", "sandbox",
  "ids", "ips", "honeybot", "honeypot", "siem", "nids", "hids",
  "waf", "dast", "sast", "vulnerability", "exploit", "0day",
  "logjam", "heartbleed", "shellshock", "poodle", "spectre",
  "meltdown", "rowhammer", "sca", "padding", "oracle"
];

// List of adjectives
// prettier-ignore
const adjs = [
  "beautiful", "creative", "dangerous", "elegant", "fancy",
  "gorgeous", "handsome", "intelligent", "jolly", "kind", "lovely",
  "magnificent", "nice", "outstanding", "perfect", "quick",
  "reliable", "smart", "talented", "unique", "vibrant", "wonderful",
  "young", "zany", "amazing", "brave", "calm", "delightful", "eager",
  "faithful", "gentle", "happy", "incredible", "jovial", "keen",
  "lucky", "merry", "optimistic", "proud", "quiet",
  "scary", "thoughtful", "upbeat", "victorious", "witty",
  "zealous", "adorable", "brilliant", "charming", "daring",
  "fearless", "graceful", "honest", "lively", "modest",
  "silly"
];

/**
 * Generates a unique cybersecurity-themed session name.
 * @returns A randomly generated session name (e.g., "brave-firewall").
 */
export function generateSessionName(): string {
  const adj = adjs[Math.floor(Math.random() * adjs.length)];
  const term = terms[Math.floor(Math.random() * terms.length)];
  return `${adj}-${term}`;
}
