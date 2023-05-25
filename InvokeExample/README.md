# C# Invoke Example

An example of calling the Nyckel `/invoke` endpoint in C# using different techniques for sending data:

1. Sequential calls using a url
2. Parallel calls using a url
3. Sequential calls sending the data inline with a dataUri
4. Parallel calls sending the data inline with a dataUri

## One time setup

### Install dotnet framework

This example uses dotnet 7; you can either install dotnet 7 to run the sample, or modify the `.csproj` file to use your preferred runtime version by changing the `TargetFramework` property.

### Populate config file

To run the sample, you'll need to provide an accessToken, functionId, and imageUrl, and update the `config.json` file accordingly.

## Running the example

From the project directory, run

    dotnet run

## Example output

If the example ran successfully, the output will look similar to the following:

    10 sequential image urls: 6,374ms
    10 parallel image urls: 1,764ms
    10 sequential dataUris: 5,617ms
    10 parallel dataUris: 1,600ms

Note that these timings will change depending on the size of your image and network latencies between the image server, the Nyckel server, and your local machine.
