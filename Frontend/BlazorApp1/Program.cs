
using BlazorApp1.Components;
using Microsoft.Extensions.DependencyInjection;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();
// Program.cs

// Register HttpClient for making API calls
builder.Services.AddHttpClient("Backend", client =>
{
    client.BaseAddress = new Uri("https://academic-research-mix-cactus.onrender.com"); // Replace with your backend base URL
});

var app = builder.Build();

// Configure the HTTP request pipeline
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    app.UseHsts();
}

app.UseHttpsRedirection();

// Static assets and antiforgery
app.UseAntiforgery();

app.MapStaticAssets();

// Map Razor components
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();

