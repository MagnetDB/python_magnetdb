Setting up a **Rule Chain** (often referred to as **Combination Selection** or **Authentication Stacking**) in LemonLDAP::NG is a powerful way to handle multiple identity sources or enforce specific conditions before a user can log in.

Since you're working with authentication rules, you're likely aiming to either provide a choice (e.g., "Login with LDAP or SAML") or a fallback mechanism.

### 1. Understanding the Logic

In LemonLDAP::NG, you define these in the **Manager** under **General Parameters** > **Authentication modules**. To use a chain, you typically set the main authentication/userdb/password modules to **Combination**.

The syntax generally follows this pattern:
`[Condition] ? Module1 : Module2`

### 2. Common Configuration Scenarios

| Use Case | Rule Syntax Example | Description |
| --- | --- | --- |
| **Simple Choice** | `$_authChoice eq "LDAP" ? LDAP : SAML` | Shows a dropdown on the login page for the user to pick their method. |
| **IP-Based Auth** | `inSubnet($ip, '192.168.1.0/24') ? LDAP : Kerberos` | Users on the local network get Kerberos; others get LDAP. |
| **Multi-Factor (MFA)** | `LDAP and TOTP` | Users must pass LDAP first, then provide a TOTP token. |
| **Domain Splitting** | `$_mail =~ /@company.com$/ ? LDAP : ExternalDB` | Routes users based on the email domain they enter. |

---

### 3. Step-by-Step Setup

1. **Enable Combination:**
* Open the Manager.
* Go to **General Parameters** > **Authentication modules**.
* Set **Authentication module**, **Users module**, and **Password module** to **Combination**.


2. **Define the Modules:**
* Go to **General Parameters** > **Authentication modules** > **Combination parameters** > **Combination modules**.
* Add your modules here (e.g., `LDAP`, `SAML`, `DBI`). Give each a name and configure its specific settings (URL, Bind DN, etc.).


3. **Set the Rule:**
* Go to **Combination parameters** > **Combinations**.
* Click **Add** and enter your logic string.
* *Example:* `[LDAP] and [TOTP]` or `$_authChoice` logic.



### 4. Important Tips

* **Variable Names:** Use `$_authChoice` if you want the user to select from a list. You must define these choices in the **Auth Choice Modules** section.
* **Case Sensitivity:** Module names in your rule (like `LDAP`) must exactly match the name you gave them in the Combination Modules list.
* **Testing:** Use the `lemonldap-ng-cli` or the "Test" button in the Manager to validate your Perl-style expressions before applying them to production.

---

> **Note:** If you are trying to implement **2FA/MFA**, LemonLDAP::NG has a specific "Second Factor" section that is often easier to manage than building a manual chain for every user.

**Would you like me to help you write a specific Perl expression for a complex login condition you're trying to meet?**
