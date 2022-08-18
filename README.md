# umbrella-reporting

get reports from reporting api
 
## Use Case Description

Describe the problem this code addresses, how your code solves the problem, challenges you had to overcome as part of the solution, and optional ideas you have in mind that could further extend your solution.

## Installation

Detailed instructions on how to install, configure, and get the project running. Call out any dependencies. This should be frequently tested and updated to make sure it works reliably, accounts for updated versions of dependencies, etc.

## Configuration

Please enter Org_ID and the Base64 string (echo '<apikey>:<apisecret>' | base64) into the file .env in the local directory.

Example:

ORG_ID=12345678
BASIC_TOKEN=<your base64-string>


## Usage

python umbrella.py -f="<time>" -t="<time>"

Time could be a timestamp or relative time string (for example: 'now', '-7days'). Please be consistent with timestamp/relative date and use either of them.

Example:

python umbrella.py -f="-42days" -t "now"

Deployment-Status between -40days and now
|           Label           | Active | Count |
|---------------------------|--------|-------|
| Anyconnect Roaming Client |   0    |   1   |
|           Sites           |   0    |   2   |
|     Roaming Computers     |   10   |  13   |
|       Organization        |   0    |   1   |
|         AD Users          |   0    |  23   |
|         Networks          |   1    |   1   |

### DevNet Sandbox

does not work with the devnet sandbox at the moment.

## How to test the software

Unfortunatly this code does not work with the Devnet Sandbox due to authorization failure.
Please use your own Umbrella instance and credentials

## Known issues

- "From-date" and "To-Date" can be provided on commandline. Unfortunatly negative numbers are treated as an option, so please use a "=" between option and value (-f="-3minutes")

- It is possible to forward either timestamp or a relative time as a value for the date (to and from). Please be consistent and either use timestamps or relative time for both values.

## Getting help

Instruct users how to get help with this code; this might include links to an issues list, wiki, mailing list, etc.

**Example**

If you have questions, concerns, bug reports, etc., please create an issue against this repository.

## Getting involved


## Author(s)

This project was written and is maintained by the following individuals:

* Mira Eilenstein <eilenstein@nscon.de>
