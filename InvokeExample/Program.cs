using System.Diagnostics;
using System.Text.Json;

var config = JsonSerializer.Deserialize<Config>(File.ReadAllText("config.json")) ?? throw new InvalidOperationException("Could not read config file");

using var client = new NyckelInvokeClient(config.accessToken, config.functionId);
using var dataUriGenerator = new DataUriGenerator();
var dataUri = await dataUriGenerator.GenerateFromUrl(config.imageUrl, "application/octet-stream");

Stopwatch timer = new Stopwatch();
int iterations = 10;
var labelIds = new List<string>();
var tasks = new List<Task>();

Console.WriteLine("Running examples...");

Console.Write($"{iterations} sequential image urls: ");
timer.Restart();
labelIds.Clear();
tasks.Clear();
for (var index = 0; index < iterations; index++)
{
    labelIds.Add(await client.Invoke(config.imageUrl));
}
timer.Stop();
Console.WriteLine($"{timer.ElapsedMilliseconds:n0}ms");

Console.Write($"{iterations} parallel image urls: ");
timer.Restart();
labelIds.Clear();
tasks.Clear();
for (var index = 0; index < iterations; index++)
{
    tasks.Add(Task.Run(async () => labelIds.Add(await client.Invoke(config.imageUrl))));
}
await Task.WhenAll(tasks);
timer.Stop();
Console.WriteLine($"{timer.ElapsedMilliseconds:n0}ms");

Console.Write($"{iterations} sequential dataUris: ");
timer.Restart();
labelIds.Clear();
tasks.Clear();
for (var index = 0; index < iterations; index++)
{
    labelIds.Add(await client.Invoke(dataUri));
}
timer.Stop();
Console.WriteLine($"{timer.ElapsedMilliseconds:n0}ms");

Console.Write($"{iterations} parallel dataUris: ");
timer.Restart();
labelIds.Clear();
tasks.Clear();
for (var index = 0; index < iterations; index++)
{
    tasks.Add(Task.Run(async () => labelIds.Add(await client.Invoke(dataUri))));
}
await Task.WhenAll(tasks);
timer.Stop();
Console.WriteLine($"{timer.ElapsedMilliseconds:n0}ms");

internal record Config(string accessToken, string functionId, string imageUrl);
