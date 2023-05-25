using System.Net.Http.Headers;
using System.Net.Http.Json;

public class NyckelInvokeClient : IDisposable
{
    private string _endpointUri;
    private HttpClient _httpClient;

    public NyckelInvokeClient(string accessToken, string functionId)
    {
        _endpointUri = $"https://www.nyckel.com/v1/functions/{functionId}/invoke";
        _httpClient = new();
        _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
    }

    public void Dispose()
    {
        _httpClient.Dispose();
    }

    public async Task<string> Invoke(string imageUri)
    {
        var response = await _httpClient.PostAsJsonAsync<InvokeRequest>(_endpointUri, new(imageUri));
        if (!response.IsSuccessStatusCode) throw new InvalidOperationException($"Call to Nyckel failed with status code {(int)response.StatusCode} {response.StatusCode}");
        var invokeResponse = await response.Content.ReadFromJsonAsync<InvokeResponse>();
        if (invokeResponse is null) throw new InvalidOperationException("Could not deserialize the response from Nyckel");
        return invokeResponse.labelId;
    }

    internal record InvokeRequest(string data);
    internal record InvokeResponse(string labelId);
}