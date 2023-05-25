public class DataUriGenerator : IDisposable
{
    private HttpClient _httpClient;

    public DataUriGenerator()
    {
        _httpClient = new();
    }

    public void Dispose()
    {
        _httpClient.Dispose();
    }

    public async Task<string> GenerateFromUrl(string imageUri, string mimeType)
    {
        var content = await _httpClient.GetByteArrayAsync(imageUri);
        var base64Data = Convert.ToBase64String(content);
        return $"data:{mimeType};base64,{base64Data}";
    }
}