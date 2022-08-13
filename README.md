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

Time could be a timestamp or relative time string (for example: 'now', '-7days'). 

### DevNet Sandbox

does not work with the devnet sandbox at the moment.

## How to test the software

Provide details on steps to test, versions of components/dependencies against which code was tested, date the code was last tested, etc. 
If the repo includes automated tests, detail how to run those tests.
If the repo is instrumented with a continuous testing framework, that is even better.


## Known issues


## Getting help

Instruct users how to get help with this code; this might include links to an issues list, wiki, mailing list, etc.

**Example**

If you have questions, concerns, bug reports, etc., please create an issue against this repository.

## Getting involved

This section should detail why people should get involved and describe key areas you are currently focusing on; e.g., trying to get feedback on features, fixing certain bugs, building important pieces, etc. Include information on how to setup a development environment if different from general installation instructions.

General instructions on _how_ to contribute should be stated with a link to [CONTRIBUTING](./CONTRIBUTING.md) file.

## Author(s)

This project was written and is maintained by the following individuals:

* Mira Eilenstein <eilenstein@nscon.de>
