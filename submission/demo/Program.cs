using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using demo;
using demo.Models;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");

var browserBase = new Uri(builder.HostEnvironment.BaseAddress);
var backendBase = new UriBuilder(browserBase) { Port = 5100, Path = "" }.Uri;
builder.Services.AddScoped(_ => new HttpClient { BaseAddress = backendBase });
// The local backend owns simulator execution. The browser never receives
// credentials and never launches Python directly.
builder.Services.AddSingleton<DemoConversationService>();
builder.Services.AddSingleton<IAgentConversation>(sp => sp.GetRequiredService<DemoConversationService>());
builder.Services.AddSingleton<WorkbenchState>();

await builder.Build().RunAsync();
