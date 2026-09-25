using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using demo;
using demo.Models;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");

builder.Services.AddScoped(sp => new HttpClient { BaseAddress = new Uri(builder.HostEnvironment.BaseAddress) });
// The submission surface is receipt-backed and credential-free. A live Foundry
// transport can replace this registration without changing human review.
builder.Services.AddSingleton<DemoConversationService>();
builder.Services.AddSingleton<IAgentConversation>(sp => sp.GetRequiredService<DemoConversationService>());

await builder.Build().RunAsync();
