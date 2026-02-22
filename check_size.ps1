Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile("C:/Users/msh17/.gemini/antigravity/brain/5e2f8ef1-faff-44e0-899e-9997cb582577/uploaded_image_1769505088547.png")
Write-Output "Width: $($img.Width) Height: $($img.Height)"
$img.Dispose()
