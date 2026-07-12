# PortSwigger Web Security Academy - Solved Labs

![Total Labs](https://img.shields.io/badge/Total%20Labs%20Solved-39-blue) ![Last Updated](https://img.shields.io/badge/Last%20Updated-2026--07--12-yellow) ![Level](https://img.shields.io/badge/Level-NEWBIE-green) ![Vulnerability labs](https://img.shields.io/badge/Completed-13.7%25-purple)
ch
This file tracks my progress through [PortSwigger Web Security Academy](https://portswigger.net/web-security) labs. I focus on web app pentesting, documenting key labs as full writeups (linked below) and logging all solves here for reference. Full writeups are reserved for first-time techniques, complex exploits, or custom tools.

## Level progress

- **Apprentice**: 10 of 61
- **Practitioner**: 29 of 174
- **Expert**: 0 of 39

## Categories Covered

- **Authentication vulnerabilities**: 8/14 lab
- **SQL injection**: 11/18 lab
- **Access control**: 9/13 lab
- **Path traversal**: 6/6 lab
- **Command injection**: 5/5 lab

## Notes

- **Full Writeups**: Only for significant labs (e.g., chained exploits or scripted solutions). See `platforms/portswigger/` for details.
- **Tools Used**: Burp Suite

## How to Read

- **Columns**:
  - `No`: Sequential lab number.
  - `Date`: When I solved it (YYYY-MM-DD).
  - `Topic`: Vulnerability category (e.g., API Testing, XSS).
  - `Lab Title`: Exact name from PortSwigger.
  - `Difficulty`: Apprentice, Practitioner, or Expert.
  - `Writeup Link`: Links to full writeup (if exists) or "N/A" for quick solves.

---

## Solved Labs

| No  | Date       | Topic                          | Lab Title                                                                           | Difficulty   | Writeup Link |
| --- | ---------- | ------------------------------ | ----------------------------------------------------------------------------------- | ------------ | ------------ |
| 1   | 2026-06-15 | SQL injection                  | SQL injection vulnerability in WHERE clause allowing retrieval of hidden data       | Apprentice   | N/A          |
| 2   | 2026-06-15 | SQL injection                  | SQL injection vulnerability allowing login bypass                                   | Apprentice   | N/A          |
| 3   | 2026-06-16 | SQL injection                  | SQL injection UNION attack, determining the number of columns returned by the query | Practitioner | N/A          |
| 4   | 2026-06-18 | SQL injection                  | SQL injection UNION attack, finding a column containing text                        | Practitioner | N/A          |
| 5   | 2026-06-18 | SQL injection                  | SQL injection UNION attack, retrieving data from other tables                       | Practitioner | N/A          |
| 6   | 2026-06-18 | SQL injection                  | SQL injection UNION attack, retrieving multiple values in a single column           | Practitioner | N/A          |
| 7   | 2026-06-18 | SQL injection                  | SQL injection attack, querying the database type and version on MySQL and Microsoft | Practitioner | N/A          |
| 8   | 2026-06-18 | SQL injection                  | SQL injection attack, listing the database contents on non-Oracle databases         | Practitioner | N/A          |
| 9   | 2026-06-20 | SQL injection                  | Blind SQL injection with conditional responses                                      | Practitioner | N/A          |
| 10  | 2026-06-20 | SQL injection                  | Blind SQL injection with conditional errors                                         | Practitioner | N/A          |
| 11  | 2026-06-21 | SQL injection                  | Visible error-based SQL injection                                                   | Practitioner | N/A          |
| 12  | 2026-06-21 | Access control                 | Unprotected admin functionality                                                     | Apprentice   | N/A          |
| 13  | 2026-06-21 | Access control                 | Unprotected admin functionality with unpredictable URL                              | Apprentice   | N/A          |
| 14  | 2026-06-21 | Access control                 | User role can be modified in user profile                                           | Apprentice   | N/A          |
| 15  | 2026-06-21 | Access control                 | User ID controlled by request parameter                                             | Apprentice   | N/A          |
| 16  | 2026-06-21 | Access control                 | Insecure direct object references                                                   | Apprentice   | N/A          |
| 17  | 2026-06-28 | Authentication vulnerabilities | Username enumeration via different responses                                        | Practitioner | N/A          |
| 18 | 2026-06-28 | Authentication vulnerabilities | Username enumeration via subtly different responses | Practitioner | N/A |
| 19 | 2026-06-28 | Authentication vulnerabilities | Username enumeration via response timing | Practitioner | N/A |
| 20 | 2026-06-28 | Authentication vulnerabilities | Broken brute-force protection, IP block | Practitioner | N/A |
| 21 | 2026-06-28 | Authentication vulnerabilities | Username enumeration via account lock | Practitioner | N/A |
| 22 | 2026-06-28 | Authentication vulnerabilities | 2FA simple bypass | Apprentice | N/A |
| 23 | 2026-07-01 | Authentication vulnerabilities | 2FA broken logic | Practitioner | N/A |
| 24 | 2026-07-03 | Path traversal | File path traversal, traversal sequences blocked with absolute path bypass | Practitioner | N/A |
| 25 | 2026-07-03 | Path traversal | File path traversal, traversal sequences stripped non-recursively | Practitioner | N/A |
| 26 | 2026-07-03 | Path traversal | File path traversal, traversal sequences stripped with superfluous URL-decode | Practitioner | N/A |
| 27 | 2026-07-05 | Path traversal | File path traversal, validation of start of path | Practitioner | N/A |
| 28 | 2026-07-05 | Path traversal | File path traversal, validation of file extension with null byte bypass | Practitioner | N/A |
| 29 | 2026-07-05 | Command injection | Blind OS command injection with time delays | Practitioner | N/A |
| 30 | 2026-07-05 | Command injection | Blind OS command injection with output redirection | Practitioner | N/A |
| 31 | 2026-07-05 | Command injection | Blind OS command injection with out-of-band interaction | Practitioner | N/A |
| 32 | 2026-07-05 | Command injection | Blind OS command injection with out-of-band data exfiltration | Practitioner | N/A |
<<<<<<< HEAD

=======
| 33 | 2026-07-12 | Access control | User role controlled by request parameter | Apprentice | N/A |
| 34 | 2026-07-12 | Access control | URL-based access control can be circumvented | Practitioner | N/A |
| 35 | 2026-07-12 | Access control | Method-based access control can be circumvented | Practitioner | N/A |
| 36 | 2026-07-12 | Access control | Multi-step process with no access control on one step | Practitioner | N/A |
|24  |
>>>>>>> d710e8d (Completed: User role controlled by request parameter)


