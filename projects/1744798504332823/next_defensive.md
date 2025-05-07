### SSH Hardening (Port 2222)

*   **Change Default Port:** While using a non-standard port like 2222 provides some obscurity, it's not a strong security measure. Evaluate if a different, less common port (outside the well-known range) should be used. Consider only allowing connections from specific IP addresses via firewall rules.
*   **Disable Password Authentication:** Enforce key-based authentication only. This eliminates brute-force password attacks.
    *   Edit `/etc/ssh/sshd_config` and set `PasswordAuthentication no`.
*   **Disable Root Login:** Prevent direct root login via SSH.
    *   Edit `/etc/ssh/sshd_config` and set `PermitRootLogin no`.
*   **Implement Strong Ciphers and MACs:**  Restrict SSH to use only strong and secure ciphers and MAC algorithms.
    *   Edit `/etc/ssh/sshd_config` and specify `Ciphers` and `MACs`.  Use recommendations from security best practices.
*   **Update SSH:**  While OpenSSH 8.2p1 is relatively recent, regularly check for updates and apply patches for security vulnerabilities.
*   **Implement Fail2ban/CrowdSec:** Automatically block IP addresses that exhibit malicious behavior (e.g., excessive failed login attempts).

### Joomla Vulnerability Mitigation (Joomla 3.4.3)

*   **Immediate Upgrade:** Upgrade Joomla to the latest stable version.  Joomla 3.4.3 is vulnerable to a critical SQL Injection vulnerability (CVE-2015-7247). Upgrading is the primary and most important mitigation.
*   **Temporary Mitigation (If Upgrade is Delayed):** If an immediate upgrade is not possible, apply the patch referenced in the exploit database entry ([https://www.exploit-db.com/exploits/38534/](https://www.exploit-db.com/exploits/38534/)) as an immediate, temporary solution. *However, this is not a replacement for a full upgrade.*
*   **Web Application Firewall (WAF):** Deploy a WAF in front of the Joomla installation.  Configure the WAF with rulesets designed to protect against common Joomla vulnerabilities, including SQL Injection and Remote File Inclusion (RFI).
*   **Review Extensions:** Audit all installed Joomla extensions.  Outdated or vulnerable extensions are a common attack vector.  Remove any unused extensions and update the remaining ones to the latest versions.

### Account Security: club@uclaestrella.es

*   **Password Reset:**  Immediately force a password reset for the `club@uclaestrella.es` account.  The user *must* create a strong, unique password.
*   **Multi-Factor Authentication (MFA):**  Implement MFA for all critical accounts, including `club@uclaestrella.es`.  This adds an extra layer of security even if the password is compromised.
*   **Password Manager Training:**  Educate the user of the `club@uclaestrella.es` account (and all users) on the importance of using a password manager to generate and store strong, unique passwords.
*   **Account Monitoring:** Monitor activity from the `club@uclaestrella.es` account for any suspicious behavior.

### Exposed Directories

*   **Restrict Access:** Review each of the listed directories (e.g., `/libraries`, `/language`, `/layouts`, `/plugins`, `/tmp`, `/cache`, `/administrator`, `/includes`, `/cli`, `/components`, `/modules`, `/logs`, `/bin`, `/installation`) and determine which ones need to be publicly accessible.
*   **.htaccess Restrictions:**  For directories that should *not* be publicly accessible, create or modify `.htaccess` files to deny access.  For example:
    ```
    Order Deny,Allow
    Deny from all
    ```
*   **Remove Installation Directory:** Ensure the `/installation` directory is removed if it exists.  This directory should only be present during the initial installation of Joomla.
*   **Move Logs Directory:** If possible, move the `/logs` directory outside the web root or otherwise restrict access to it. Sensitive information may be stored in log files.
*   **Protect administrator Directory:** Consider IP whitelisting for access to the `/administrator` directory, or using a strong, randomly-generated directory name for the admin panel.

### General Security Hardening

*   **Aruba Proxy Review:** Investigate the Aruba proxy server configuration.  Ensure it is properly secured and not vulnerable to any known exploits.  Keep the proxy software up to date.
*   **Regular Security Audits:** Conduct regular vulnerability scans and penetration tests to identify and address security weaknesses.
*   **Security Awareness Training:**  Provide regular security awareness training to all users to educate them about phishing, social engineering, and other common security threats.
*   **Monitor DMARC Reports:**  Regularly monitor DMARC reports to identify and address email spoofing attempts.
*   **Firewall Configuration:** Ensure the firewall is properly configured to block unnecessary ports and services. Only allow explicitly required traffic.
*   **Implement Intrusion Detection/Prevention System (IDS/IPS):** Deploy an IDS/IPS to detect and prevent malicious activity on the network.