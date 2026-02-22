
Add-Type -AssemblyName System.Drawing

$inputPath = "C:/Users/msh17/.gemini/antigravity/brain/5e2f8ef1-faff-44e0-899e-9997cb582577/uploaded_image_1769505088547.png"
$outputPath = "C:/Users/msh17/.gemini/antigravity/brain/5e2f8ef1-faff-44e0-899e-9997cb582577/banner_edited.png"
# Text to add
$text = "전화상담 가능 시간 : 평일 오전 10시 ~ 오후 6시"

# Load image
$image = [System.Drawing.Image]::FromFile($inputPath)
$graphics = [System.Drawing.Graphics]::FromImage($image)

# High quality rendering
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

# Font settings
$fontScale = 14
$font = New-Object System.Drawing.Font("Malgun Gothic", $fontScale, [System.Drawing.FontStyle]::Regular)
$brush = [System.Drawing.Brushes]::White

# Layout settings
$format = New-Object System.Drawing.StringFormat
$format.Alignment = [System.Drawing.StringAlignment]::Center
$format.LineAlignment = [System.Drawing.StringAlignment]::Far

# Define a rectangle for the entire image, with a small padding at the bottom
# The text will be drawn at the bottom center of this rectangle
$rect = New-Object System.Drawing.RectangleF(0, 0, $image.Width, $image.Height - 8)

# Draw string
$graphics.DrawString($text, $font, $brush, $rect, $format)

# Save
$image.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)

# Cleanup
$graphics.Dispose()
$image.Dispose()

Write-Output "Successfully created $outputPath"
