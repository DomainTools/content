The RSA Archer GRC platform provides a common foundation for managing policies, controls, risks, assessments and deficiencies across lines of business.

## Configure RSA Archer v2 in Cortex

1. Navigate to **Settings** > **Integrations** > **Servers & Services**.
2. Search for RSA Archer v2.
3. Click **Add instance** to create and configure a new integration instance.

    | **Parameter** | **Description** | **Required** |
    | --- | --- | --- |
    | Server URL | For example: https://192.168.0.1/rsaarcher, https://192.168.0.1/, or https://192.168.0.1/archer. | True |
    | API Endpoint | Change only if using another API endpoint. | True |
    | Username | | True |
    | Fetch incidents | | False |
    | Incident type | | False |
    | Trust any certificate (not secure) | | False |
    | Use system proxy settings | | False |
    | Timeout | Request timeout value in seconds. Default is 400. | False |
    | Instance name | | True |
    | User domain | | False |
    | Application ID for fetch | | True |
    | Application date field for fetch | The value should be the field name. Default is Date/Time Occurred. | True |
    | Maximum number of incidents to pull per fetch | Default is 10. | False |
    | First fetch timestamp | Time from which to begin fetching incidents in the `<number> <time unit>` format. For example: 12 hours, 7 days, 3 months, 1 year. | False |
    | List of fields from the application to get into the incident | A comma-separated list of application field names. For example: `Date/Time Occurred,Days Open`. | False |
    | XML for fetch filtering | Additional XML condition element(s) to use when fetching. Using a "DateComparisonFilterCondition" element is not supported. For more information, check the "Limitations" section of the documentation. | False |

4. Click **Test** to validate the URLs, token, and connection.

### Limitations

- The "XML for fetch filtering" configuration parameter cannot contain "DateComparisonFilterCondition" XML element since it would interfere with the existing fetch date filter. Other types of filtering conditions, such as "TextFilterCondition", are allowed.

- Archer customers might know there is an Archer REST API that supports token based authentication. Not all functionality of this integration can be achieved using Archer's REST API, which is why this integration requires credential based authentication.

## Commands

You can execute these commands from the Cortex XSOAR CLI as part of an automation or in a playbook.
After you successfully execute a command, a DBot message appears in the War Room with the command details.

### archer-search-applications

***
Gets application details or list of all applications.

#### Base Command

`archer-search-applications`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| applicationId | The application ID to get details for. Leave empty to get a list of all applications. | Optional | 

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Archer.Application.Guid | String | The application GUID. | 
| Archer.Application.Id | Number | The unique ID of the application. | 
| Archer.Application.Status | Number | The application Status. | 
| Archer.Application.Type | Number | The application type. | 
| Archer.Application.Name | String | The application name. | 

#### Command Example

```!archer-search-applications applicationId=75```

#### Context Example

```json
{
    "Archer": {
        "Application": {
            "Guid": "982fc3be-7c43-4d79-89a1-858ed262b930",
            "Id": 75,
            "LanguageId": 1,
            "Name": "Incidents",
            "Status": 1,
            "Type": 2
        }
    }
}
```

#### Human Readable Output

>### Search applications results

>|Guid|Id|LanguageId|Name|Status|Type|
>|---|---|---|---|---|---|
>| 982fc3be-7c43-4d79-89a1-858ed262b930 | 75 | 1 | Incidents | 1 | 2 |


### archer-get-application-fields

***
Gets all application fields by application ID.

#### Base Command

`archer-get-application-fields`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| applicationId | The application ID to get the application fields for. | Required | 

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Archer.ApplicationField.FieldId | Number | The unique ID of the field. | 
| Archer.ApplicationField.FieldName | String | The field name. | 
| Archer.ApplicationField.FieldType | String | The field type. | 
| Archer.ApplicationField.LevelID | Number | The field level ID. | 

#### Command Example

```!archer-get-application-fields applicationId=75```

#### Context Example

```json
{
    "Archer": {
        "ApplicationField": [
            {
                "FieldId": 296,
                "FieldName": "Incident ID",
                "FieldType": "TrackingID",
                "LevelID": 67
            },
            {
                "FieldId": 297,
                "FieldName": "Date Created",
                "FieldType": "First Published",
                "LevelID": 67
            },
            {
                "FieldId": 298,
                "FieldName": "Last Updated",
                "FieldType": "Last Updated Field",
                "LevelID": 67
            },
            {
                "FieldId": 302,
                "FieldName": "Status",
                "FieldType": "Values List",
                "LevelID": 67
            },
            {
                "FieldId": 303,
                "FieldName": "Date/Time Occurred",
                "FieldType": "Date",
                "LevelID": 67
            },
            {
                "FieldId": 304,
                "FieldName": "Priority",
                "FieldType": "Values List",
                "LevelID": 67
            }
        ]
    }
}
```

#### Human Readable Output

>### Application fields

>|FieldId|FieldName|FieldType|LevelID|
>|---|---|---|---|
>| 296 | Incident ID | TrackingID | 67 |
>| 297 | Date Created | First Published | 67 |
>| 298 | Last Updated | Last Updated Field | 67 |
>| 302 | Status | Values List | 67 |
>| 303 | Date/Time Occurred | Date | 67 |
>| 304 | Priority | Values List | 67 |

### archer-get-field

***
Returns a mapping from list value name to list value ID.

#### Base Command

`archer-get-field`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| fieldID | The ID of the field. | Required | 

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Archer.ApplicationField.FieldId | Number | The unique ID of the field. | 
| Archer.ApplicationField.FieldName | String | The field name. | 
| Archer.ApplicationField.FieldType | String | The field type. | 
| Archer.ApplicationField.LevelID | Number | The field level ID. | 

#### Command Example

```!archer-get-field fieldID=350```

#### Context Example

```json
{
    "Archer": {
        "ApplicationField": {
            "FieldId": 350,
            "FieldName": "Reported to Police",
            "FieldType": "Values List",
            "LevelID": 67
        }
    }
}
```

#### Human Readable Output

>### Application field

>|FieldId|FieldName|FieldType|LevelID|
>|---|---|---|---|
>| 350 | Reported to Police | Values List | 67 |

### archer-get-mapping-by-level

***
Returns a mapping of fields by level ID.

#### Base Command

`archer-get-mapping-by-level`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| level | The ID of the level. | Required | 


#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Archer.LevelMapping.Id | Number | The unique ID of the field. | 
| Archer.LevelMapping.Name | String | The field name. | 
| Archer.LevelMapping.Type | String | The field type. | 
| Archer.LevelMapping.LevelId | Number | The field level ID. | 

#### Command Example

```!archer-get-mapping-by-level level=67```

#### Context Example

```json
{
    "Archer": {
        "LevelMapping": [
            {
                "Id": 296,
                "LevelId": 67,
                "Name": "Incident ID",
                "Type": "TrackingID"
            },
            {
                "Id": 297,
                "LevelId": 67,
                "Name": "Date Created",
                "Type": "First Published"
            },
            {
                "Id": 298,
                "LevelId": 67,
                "Name": "Last Updated",
                "Type": "Last Updated Field"
            },
            {
                "Id": 302,
                "LevelId": 67,
                "Name": "Status",
                "Type": "Values List"
            }
        ]
    }
}
```

#### Human Readable Output

>### Level mapping for level 67

>|Id|LevelId|Name|Type|
>|---|---|---|---|
>| 296 | 67 | Incident ID | TrackingID |
>| 297 | 67 | Date Created | First Published |
>| 298 | 67 | Last Updated | Last Updated Field |
>| 302 | 67 | Status | Values List |

### archer-get-record

***
Gets information about a content record in the given application.

#### Base Command

`archer-get-record`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| contentId | The content record ID. | Required | 
| applicationId | The application ID. | Required | 

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Archer.Record.Id | Number | The unique ID of the content record. | 

#### Command Example

```!archer-get-record applicationId=75 contentId=227602```

#### Context Example

```json
{
    "Archer": {
        "Record": {
            "Current Status": {
                "OtherText": null,
                "ValuesListIds": [
                    6412
                ]
            },
            "Date/Time Occurred": "2018-03-23T07:00:00",
            "Date/Time Reported": "2018-03-26T10:03:32.243",
            "Days Open": 805,
            "Default Record Permissions": {
                "GroupList": [
                    {
                        "HasDelete": true,
                        "HasRead": true,
                        "HasUpdate": true,
                        "Id": 50
                    },
                    {
                        "HasDelete": false,
                        "HasRead": true,
                        "HasUpdate": false,
                        "Id": 51
                    }
                ],
                "UserList": []
            },
            "Google Map": "<a target='_new' href='http://maps.google.com/maps?f=q&ie=UTF8&om=1&hl=en&q=, , , '>Google Map</a>",
            "Id": 227602,
            "Incident Details": "Incident Details",
            "Incident Result": {
                "OtherText": null,
                "ValuesListIds": [
                    531
                ]
            },
            "Incident Summary": "Summary...",
            "Is BSA (Bank Secrecy Act) reporting required in the US?": {
                "OtherText": null,
                "ValuesListIds": [
                    835
                ]
            },
            "Notify Incident Owner": {
                "OtherText": null,
                "ValuesListIds": [
                    6422
                ]
            },
            "Override Rejected Submission": {
                "OtherText": null,
                "ValuesListIds": [
                    9565
                ]
            },
            "Status": {
                "OtherText": null,
                "ValuesListIds": [
                    466
                ]
            },
            "Status Change": {
                "OtherText": null,
                "ValuesListIds": [
                    156
                ]
            },
            "Supporting Documentation": [
                125
            ]
        }
    }
}
```

#### Human Readable Output

>### Record details

>|Current Status|Date/Time Occurred|Date/Time Reported|Days Open|Default Record Permissions|Google Map|Id|Incident Details|Incident Result|Incident Summary|Is BSA (Bank Secrecy Act) reporting required in the US?|Notify Incident Owner|Override Rejected Submission|Status|Status Change|Supporting Documentation|
>|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
>| ValuesListIds: 6412<br/>OtherText: null | 2018-03-23T07:00:00 | 2018-03-26T10:03:32.243 | 805.0 | UserList: <br/>GroupList: {'Id': 50, 'HasRead': True, 'HasUpdate': True, 'HasDelete': True},<br/>{'Id': 51, 'HasRead': True, 'HasUpdate': False, 'HasDelete': False} | <a target='_new' href='http://maps.google.com/maps?f=q&ie=UTF8&om=1&hl=en&q=, , , '>Google Map</a> | 227602 | Incident Details | ValuesListIds: 531<br/>OtherText: null | Summary... | ValuesListIds: 835<br/>OtherText: null | ValuesListIds: 6422<br/>OtherText: null | ValuesListIds: 9565<br/>OtherText: null | ValuesListIds: 466<br/>OtherText: null | ValuesListIds: 156<br/>OtherText: null | 125 |

### archer-create-record

***
Creates a new content record in the given application.

Note: When creating a new record, make sure the values are sent through the *fieldsToValues* argument properly.

- Example for the *Values List* field type: {"Type": ["Switch"], fieldname: [value1, value2]}
- Example for the *Values List* field type with *OtherText* property: {"Patch Type": {"ValuesList": ["Custom Type"], "OtherText": "actuall text"}, field_name_without_other: [value1, value2]}
- Example for the *External Links* field type: {"Patch URL": [{"value":"github", "link": "https://github.com"}]}
- Example for the *Users/Groups List* field type: {"Policy Owner":{"users": [20],"groups": [30]}}
- Example for the *Cross- Reference* field type: {"Area Reference(s)": [20]}

In other cases the value can be sent as-is.

To determine the appropriate field type value, use the `archer-get-application-fields` command with the `applicationId` to get the list of all *FieldType* by *FieldName*.

#### Base Command

`archer-create-record`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| applicationId | The application ID. | Required | 
| fieldsToValues | Record fields in JSON format: { "Name1": Value1, "Name2": Value2 }. Field names are case sensitive. | Required | 
| levelId | The Level ID to use to update the record. If empty, the command by default takes the first level ID. | Optional |

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Archer.Record.Id | Number | The unique ID of the content record. | 

#### Command Example

`!archer-create-record applicationId=75 fieldsToValues={"Incident Summary":"This is the incident summary","Priority":["High"]}`

#### Context Example

```json
{
    "Archer": {
        "Record": {
            "Id": 239643
        }
    }
}
```

#### Human Readable Output

>Record created successfully, record id: 239643

### archer-delete-record

***
Deletes an existing content record in the given application.

#### Base Command

`archer-delete-record`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| contentId | The ID of the content record to delete. | Required | 

#### Context Output

There is no context output for this command.

#### Command Example

```!archer-delete-record contentId=239642```

#### Context Example

```json
{}
```

#### Human Readable Output

>Record 239642 deleted successfully

### archer-update-record

***
Updates an existing content record in the given application.
Note: When updating a record, make sure the values are sent through the *fieldsToValues* argument properly. For more details see the archer-create-record description.

#### Base Command

`archer-update-record`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| applicationId | The application ID. | Required | 
| fieldsToValues | Record fields in JSON format: { "Name1": Value1, "Name2": Value2 }. Field name is case sensitive | Required | 
| contentId | The ID of the content record ID. | Required | 
| levelId | The Level ID to use to update the record. If empty, the command by default takes the first level ID. | Optional |

#### Context Output

There is no context output for this command.

#### Command Example

`!archer-update-record applicationId=75 contentId=239326 fieldsToValues={"Priority":["High"]}`

#### Context Example

```json
{}
```

#### Human Readable Output

>Record 239326 updated successfully

### archer-execute-statistic-search-by-report

***
Performs statistic search by report GUID.

#### Base Command

`archer-execute-statistic-search-by-report`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| reportGuid | The report GUID. | Required | 
| maxResults | Maximum number of pages for the reports. | Required | 

#### Context Output

There is no context output for this command.

#### Command Example

```!archer-execute-statistic-search-by-report maxResults=100 reportGuid=e4b18575-52c0-4f70-b41b-3ff8b6f13b1c```

#### Context Example

```json
{}
```

#### Human Readable Output

>{
>  "Groups": {
>    "@count": "3",
>    "Metadata": {
>      "FieldDefinitions": {
>        "FieldDefinition": [
>          {
>            "@alias": "Classification",
>            "@guid": "769b2548-6a98-49b6-95c5-03e391f0a40e",
>            "@id": "76",
>            "@name": "Classification"
>          },
>          {
>            "@alias": "Standard_Name",
>            "@guid": "a569fd34-16f9-4965-93b0-889fcb91ba7a",
>            "@id": "1566",
>            "@name": "Standard Name"
>          }
>        ]
>      }
>    },
>    "Total": {
>      "Aggregate": {
>        "@Count": "1497",
>        "@FieldId": "1566"
>      }
>    }
>  }
>}

### archer-get-reports

***
Gets all reports from Archer.

#### Base Command

`archer-get-reports`

#### Input

There are no input arguments for this command.

#### Context Output

There is no context output for this command.

#### Command Example

```archer-get-reports```

#### Context Example

```json
{
    "Archer": {
        "Report": [
            {
                "ApplicationGUID": "982fc3be-7c43-4d79-89a1-858ed262b930",
                "ApplicationName": "Policies",
                "ApplicationDescription": "This report displays a listing of all security Policies.",
                "ReportGUID": "22961b81-4866-40ea-a298-99afb348598d",
                "ReportName": "Policies - Summary view"
            }
        ]
    }
}
```

#### Human Readable Output

### archer-get-search-options-by-guid

***
Returns search criteria by report GUID.

#### Base Command

`archer-get-search-options-by-guid`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| reportGuid | The report GUID. | Required | 


#### Context Output

There is no context output for this command.

#### Command Example

```!archer-get-search-options-by-guid reportGuid=bce4222c-ecfe-4cef-a556-fe746e959f12```

#### Context Example

```json
{}
```

#### Human Readable Output

>{
>  "SearchReport": {
>    "Criteria": {
>      "ModuleCriteria": {
>        "BuildoutRelationship": "Union",
>        "IsKeywordModule": "True",
>        "Module": "421",
>        "SortFields": {
>          "SortField": [
>            {
>              "Field": "15711",
>              "SortType": "Ascending"
>            },
>            {
>              "Field": "15683",
>              "SortType": "Ascending"
>            }
>          ]
>        }
>      }
>    },
>    "DisplayFields": {
>      "DisplayField": [
>        "15683",
>        "15686",
>        "15687",
>        "15690",
>        "15706",
>        "15711",
>        "15710",
>        "15712",
>        "15713",
>        "15714",
>        "15715",
>        "15716",
>        "15725",
>        "15717",
>        "15718"
>      ]
>    },
>    "PageSize": "50"
>  }
>}

### archer-reset-cache

***
Resets Archer's integration cache. This cache is maintained in XSOAR based on previous search results and must be cleared when field mappings no longer make sense. Run this command if you change the fields of your Archer application, the Archer v2 integration's settings, or if the target Archer user moves between environments or settings.

#### Base Command

`archer-reset-cache`

#### Input

There are no input arguments for this command.

#### Context Output

There is no context output for this command.

#### Command Example

```!archer-reset-cache```

#### Context Example

```json
{}
```

#### Human Readable Output


### archer-get-valuelist

***
Returns a list of values for a specified field, for example, fieldID=16114. This command is applicable only to value list fields (type 4) and will attempt to fetch the list from the internal integration instance cache. To ensure an up-to-date response, execute the `archer-reset-cache` command beforehand to clear the cache and force a new request to the API.

#### Base Command

`archer-get-valuelist`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| fieldID | The field ID. | Required |
| depth | In case of nesting, to which level to go in the depth of the recursion. Default is 0. | Optional |

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Archer.ApplicationField.ValuesList.Id | Number | The field value ID. | 
| Archer.ApplicationField.ValuesList.IsSelectable | Boolean | Specifies whether you can select the field value. | 
| Archer.ApplicationField.ValuesList.Name | String | The field value name. | 


#### Command Example

```!archer-get-valuelist fieldID=302```

#### Context Example

```json
{
    "Archer": {
        "ApplicationField": {
            "FieldId": "302",
            "ValuesList": [
                {
                    "Id": 466,
                    "IsSelectable": true,
                    "Name": "New"
                },
                {
                    "Id": 467,
                    "IsSelectable": true,
                    "Name": "Assigned"
                },
                {
                    "Id": 468,
                    "IsSelectable": true,
                    "Name": "In Progress"
                },
                {
                    "Id": 469,
                    "IsSelectable": true,
                    "Name": "On Hold"
                },
                {
                    "Id": 470,
                    "IsSelectable": true,
                    "Name": "Closed"
                }
            ]
        }
    }
}
```

#### Human Readable Output

>### Value list for field 302

>|Id|IsSelectable|Name|
>|---|---|---|
>| 466 | true | New |
>| 467 | true | Assigned |
>| 468 | true | In Progress |
>| 469 | true | On Hold |
>| 470 | true | Closed |

### archer-upload-file

***
Uploads a file to Archer. You can associate the file to a record by providing all of the following arguments:

- applicationId
- contentId
- associatedField

#### Base Command

`archer-upload-file`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| entryId | A comma seperated list of entry IDs of the files in Cortex XSOAR context. | Required | 
| contentId | The content record ID to update.| Optional | 
| applicationId | ID of the application which we want to upload the file to. | Optional | 
| associatedField | Archer field name to associate the file with. | Optional |

#### Context Output

There is no context output for this command.

#### Command Example

```!archer-upload-file entryId=16695@b32fdf18-1c65-43af-8918-7f85a1fab951```

#### Context Example

```json
{}
```

#### Human Readable Output

>File uploaded successfully, attachment ID: 126


### archer-get-file

***
Downloads a file from Archer to Cortex XSOAR War Room context.

#### Base Command

`archer-get-file`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| fileId | The file ID. | Required | 

#### Context Output

There is no context output for this command.

#### Command Example

```!archer-get-file fileId=125```

#### Context Example

```json
{
    "File": {
        "EntryID": "16680@b32fdf18-1c65-43af-8918-7f85a1fab951",
        "Extension": "jpg",
        "Info": "image/jpeg",
        "MD5": "fb80f3fc41f2524",
        "Name": "11.jpg",
        "SHA1": "6898512eaa3",
        "SHA256": "f4bed94abd752",
        "SHA512": "ecce92345fb8b6aa",
        "SSDeep": "768:XYDWR",
        "Size": 52409,
        "Type": "JPEG image data, JFIF standard 1.01, aspect ratio, density 1x1, segment length 16, progressive, precision 8, 750x561, frames 3"
    }
}
```

#### Human Readable Output

### archer-list-users

***
Gets details for a user or a list of all users.

#### Base Command

`archer-list-users`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| userId | The ID of the user to get details for. Leave empty to get a list of all users. | Optional | 

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Archer.User.AccountStatus | String | The account status of the user. | 
| Archer.User.DisplayName | String | The display name of the user. | 
| Archer.User.FirstName | String | The first name of the user. | 
| Archer.User.Id | Number | The unique ID of the user. | 
| Archer.User.LastLoginDate | Date | The last login date of user. | 
| Archer.User.LastName | String | The last name of the user. | 
| Archer.User.MiddleName | String | The middle name of the user. | 
| Archer.User.UserName | String | The username associated with the account. | 

#### Command Example

```!archer-list-users```

#### Context Example

```json
{
    "Archer": {
        "User": {
            "AccountStatus": "Locked",
            "DisplayName": "cash, johnny",
            "FirstName": "johnny",
            "Id": 202,
            "LastLoginDate": "2018-09-03T07:56:51.027",
            "LastName": "cash",
            "MiddleName": null,
            "UserName": "johnnyCash"
        }
    }
}
```

#### Human Readable Output

>### Users list

>|AccountStatus|DisplayName|FirstName|Id|LastLoginDate|LastName|MiddleName|UserName|
>|---|---|---|---|---|---|---|---|
>| Locked | cash, johnny | johnny | 202 | 2018-09-03T07:56:51.027 | cash |  | johnnyCash |

### archer-search-records

***
Search for records inside the given application

#### Base Command

`archer-search-records`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| applicationId | The ID of the application in which to search for records. | Required | 
| fieldToSearchOn | The name of the field on which to search. Leave empty to search on all fields. | Optional | 
| fieldToSearchById | The name of the primary Id field on which to search. Used instead of the fieldToSearchOn argument for searching by the application primary field. | Optional | 
| searchValue | Search value. Leave empty to search for all. | Optional | 
| maxResults | Maximum number of results to return from the search (default is 10). | Optional | 
| fieldsToDisplay | Fields to present in the search results in array format. For example, "Title,Incident Summary". | Optional | 
| numericOperator | Numeric search operator. Can be "Equals", "NotEqual", "GreaterThan", or "LessThan". | Optional | 
| dateOperator | Date search operator. Can be "Equals", "DoesNotEqual", "GreaterThan", or "LessThan". | Optional | 
| fieldsToGet | Fields to fetch from the the application. | Optional | 
| fullData | Whether to get extended responses with all of the data regarding this search. For example, "fullData=true" | Required |
| isDescending | Whether to order by descending order. Possible values are: "true", "false". | Optional |
| levelId | The Level ID to use for searching. This argument is relevant when fullData is True. If empty, the command by default takes the first level ID. | Optional |
| xmlForFiltering | The raw XML filter condition. For example: "DateComparisonFilterCondition" or "TextFilterCondition" XML element. | Optional |

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Archer.Record | Unknown | The content object. | 
| Archer.Record.Id | Number | The content record ID. | 


#### Command Example

```!archer-search-records applicationId=75 fullData=False fieldsToDisplay=`Date/Time Occurred,Days Open` fieldsToGet=`Date/Time Occurred,Days Open` fieldToSearchOn=`Date/Time Occurred` dateOperator=GreaterThan searchValue=2018-06-23T07:00:00Z xmlForFiltering=`<TextFilterCondition><Operator>Contains</Operator><Field name="Incident Priority">456</Field><Value>High</Value></TextFilterCondition>` maxResults=100```

#### Context Example

```json
{
    "Archer": {
        "Record": {
            "Date/Time Occurred": "2018-07-10T08:00:00Z",
            "Days Open": "30",
            "Id": "227664"
        }
    }
}
```

#### Human Readable Output

>### Search records results

>|Date/Time Occurred|Days Open|
>|---|---|
>| 2018-07-10T08:00:00Z | 30 |


### archer-search-records-by-report

***
Searches records by report GUID.

#### Base Command

`archer-search-records-by-report`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| reportGuid | The report GUID. | Required | 


#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| Archer.SearchByReport.ReportGUID | String | The report GUID. | 
| Archer.SearchByReport.RecordsAmount | Number | The number of records found by the search. | 
| Archer.SearchByReport.Record | Unknown | The records found by the search. | 


#### Command Example

```!archer-search-records-by-report reportGuid=bce4222c-ecfe-4cef-a556-fe746e959f12```

#### Context Example

```json
{
    "Archer": {
        "SearchByReport": {
            "Record": [
                {
                    "Description": "<p>\u00a0test_procedure_0</p>",
                    "Id": "227528",
                    "Procedure Name": "test_procedure_0",
                    "Threat Category": "Malware",
                    "Tracking ID": "227528"
                },
                {
                    "Description": "<p>\u00a0test_procedure_1</p>",
                    "Id": "227529",
                    "Procedure Name": "test_procedure_1",
                    "Threat Category": "Malware",
                    "Tracking ID": "227529"
                },
                {
                    "Description": "<p>test_procedure_2\u00a0</p>",
                    "Id": "227531",
                    "Procedure Name": "test_procedure_2",
                    "Threat Category": "Malware",
                    "Tracking ID": "227531"
                },
                {
                    "Description": "<p>test_procedure_3</p>",
                    "Id": "227532",
                    "Procedure Name": "test_procedure_3",
                    "Threat Category": "Malware",
                    "Tracking ID": "227532"
                }
            ],
            "RecordsAmount": 4,
            "ReportGUID": "bce4222c-ecfe-4cef-a556-fe746e959f12"
        }
    }
}
```

#### Human Readable Output

>### Search records by report results

>|Description|Id|Procedure Name|Threat Category|Tracking ID|
>|---|---|---|---|---|
>| <p> test_procedure_0</p> | 227528 | test_procedure_0 | Malware | 227528 |
>| <p> test_procedure_1</p> | 227529 | test_procedure_1 | Malware | 227529 |
>| <p>test_procedure_2 </p> | 227531 | test_procedure_2 | Malware | 227531 |
>| <p>test_procedure_3</p> | 227532 | test_procedure_3 | Malware | 227532 |


### archer-print-cache

***
Prints the Archer's integration cache.

#### Base Command

`archer-print-cache`

#### Input

There are no input arguments for this command.

#### Context Output

There is no context output for this command.

#### Command Example

```!archer-print-cache```

#### Context Example

```json
{}
```

#### Human Readable Output

>{
>  "75": [
>    {
>      "level": 67,
>      "mapping": {
>        "10052": {
>          "FieldId": "10052",
>          "IsRequired": false,
>          "Name": "Related Incidents (2)",
>          "RelatedValuesListId": null,
>          "Type": 23
>        },
>        "10172": {
>          "FieldId": "10172",
>          "IsRequired": false,
>          "Name": "Source",
>          "RelatedValuesListId": 1176,
>          "Type": 4
>        },
>        "10183": {
>          "FieldId": "10183",
>          "IsRequired": false,
>          "Name": "Is BSA (Bank Secrecy Act) reporting required in the US?",
>          "RelatedValuesListId": 152,
>          "Type": 4
>        },
>        "10188": {
>          "FieldId": "10188",
>          "IsRequired": false,
>          "Name": "Batch File Format",
>          "RelatedValuesListId": 1183,
>          "Type": 4
>        }
>      }
>    }
>  ],
>  "fieldValueList": {
>    "7782": {
>      "FieldId": "7782",
>      "ValuesList": [
>        {
>          "Id": 6412,
>          "IsSelectable": true,
>          "Name": "New"
>        },
>        {
>          "Id": 6413,
>          "IsSelectable": true,
>          "Name": "Assigned"
>        },
>        {
>          "Id": 6414,
>          "IsSelectable": true,
>          "Name": "In Progress"
>        },
>        {
>          "Id": 6415,
>          "IsSelectable": true,
>          "Name": "On Hold"
>        },
>        {
>          "Id": 6416,
>          "IsSelectable": true,
>          "Name": "Closed"
>        }
>      ]
>    }
>  }
>}
