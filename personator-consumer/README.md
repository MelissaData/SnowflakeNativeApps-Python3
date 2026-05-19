# Native App Personator Consumer Sample Code <!-- omit in toc -->
- [Overview](#overview)
- [Requirements](#requirements)
  - [Environments](#environments)
  - [Licensing](#licensing)
- [Instructions](#instructions)
  - [Step 1 - Choose a job](#step-1---choose-a-job)
  - [Step 2 - Configure Snowflake connection](#step-2---configure-snowflake-connection)
  - [Step 3 - Modify config.json for input](#step-3---modify-configjson-for-input)
  - [Step 4 - Run sample code using command line](#step-4---run-sample-code-using-command-line)
  - [Logs](#logs)
  - [Notes](#notes)
    - [Snowflake CLI Interactive Mode](#snowflake-cli-interactive-mode)
    - [Application Configuration](#application-configuration)
- [Contact us](#contact-us)

## Overview
The sample codes showcase features of Melissa's Native App Personator Consumer in Snowflake.

Please feel free to copy or embed this code to your own project. Happy coding!

- [Native App Personator Consumer release notes](https://releasenotes.melissa.com/software-integrations/native-app-personator-consumer-snowflake/)
- [Native App Personator Consumer documentations](https://docs.melissa.com/software/native-app-personator-consumer-for-snowflake/native-app-personator-consumer-for-snowflake-index.html)

## Requirements
### Environments
- Non-trial Snowflake account
- Windows 11 64-bit, [Python 3.13](https://www.python.org/downloads/), [Powershell 7.6](https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell-on-windows)
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation) Version 3.15.0 or later

### Licensing
All Melissa's Native Apps in Snowflake require a license in order to receive meaningful results. This license is an encrypted series of letters, numbers, and symbols. This license can also either be a Credit license or a Subscription license. Both ways use the same service, so you do not need to change your code to move from one model to another.

To learn more about how to set up a license key with Melissa, please visit [Licensing Information](https://docs.melissa.com/cloud-api/cloud-api/licensing.html).

## Instructions

### Step 1 - Choose a job
```
app-name/
    └── job-name/
```

### Step 2 - Configure Snowflake connection
Display Snowflake CLI information.

```powershell
snow --info
```

The sample code will use the default connection in ``config.toml`` to establish a connection with your Snowflake account and run queries from your local environment.


For more information, check out [Snowflake | Configuring Snowflake CLI and Connecting to Snowflake](https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/connect)

### Step 3 - Modify config.json for input
```
app-name/
    ├── job-name/
        ├── sample-code.py
        └── sample-config.json
```

### Step 4 - Run sample code using command line

```powershell
python "path/to/your/sample/code.py" --config "path/to/sample/config.json"
```

### Logs

If configured, view log messages from your test run in ``./logs/`` folder.

```
app-name/
    ├── job-name/
        ├── logs/
        ├── sample-code.py
        └── sample-config.json
```

Or query the ``event_table`` in your Snowflake account if you had it setup.
- Show ``event_table`` in your account

```powershell
snow sql --query "SHOW PARAMETERS LIKE 'event_table' IN ACCOUNT;"
```
- View summary logs from the ``event_table`` for the job done by the sample code.
```powershell
snow sql -q "
SELECT VALUE, TIMESTAMP, RECORD_TYPE, RECORD, RECORD_ATTRIBUTES
FROM <REPLACE_WITH_YOUR_EVENT_TABLE>
WHERE RECORD_TYPE = 'LOG'
  AND VALUE LIKE '%<YOUR_JOB_NAME>%'
ORDER BY TIMESTAMP DESC
LIMIT 100;
"
```
- View detailed logs from each instance call.
```powershell
snow sql -q "
SELECT
    RESOURCE_ATTRIBUTES:"snow.application.name"::STRING as APP_NAME
    ,RECORD, RECORD_ATTRIBUTES, RECORD_TYPE, TIMESTAMP
FROM <REPLACE_WITH_YOUR_EVENT_TABLE>
WHERE RECORD_TYPE LIKE 'SPAN_EVENT%'
    AND APP_NAME LIKE '<YOUR_APP_INSTANCE>'
ORDER BY TIMESTAMP DESC
LIMIT 100;
"
```

### Notes
#### Snowflake CLI Interactive Mode
You can also enter the [Interactive Mode](https://docs.snowflake.com/en/developer-guide/snowflake-cli/command-reference/sql-commands/sql#interactive-mode) of Snowflake CLI to run SQL query one at a time.

```powershell
snow sql
```

#### Application Configuration
If an app supports multiple instances, make sure to complete the **Application Configuration** step for each instance,
such as setting up the connection, privilege permission, event tracing and logging, etc.

Each instance is an independent app with its own application database, external access integration, and stored procedures.

## Contact us
You can contact our [Product Support](mailto:SnowflakeSupport@Melissa.com) or 800-MELISSA ext. 3 (800-635-4772 ext. 3) for any questions about our Snowflake Native App products.
