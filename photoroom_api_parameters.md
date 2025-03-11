# Photoroom API Parameters Documentation

This document provides a comprehensive list of parameters available for the Photoroom API based on the official documentation and code samples.

## API Plans

PhotoRoom offers two main API plans:
- **Basic plan**: Remove Background API - Simple background removal
- **Plus plan**: Image Editing API - Advanced features including AI shadows, backgrounds, relighting, and more

## Base API Endpoints

### Basic Plan (Remove Background API)
```
https://sdk.photoroom.com/v1/segment
```

### Plus Plan (Image Editing API v2)
```
https://api.photoroom.com/v2/edit
```

## Authentication

All requests must include the API key in the header:

```
x-api-key: YOUR_API_KEY
```

## Request Format

The API accepts `multipart/form-data` requests with the following structure:

- The image file should be sent as a form field named `image_file`
- Additional parameters can be included as form fields

## Available Parameters

### Basic Parameters (Available in both plans)

| Parameter | Type | Description | Possible Values | Default |
|-----------|------|-------------|-----------------|---------|
| `format` | string | Output image format | `png`, `jpg`, `webp` | `png` |
| `bg_color` | string | Background color (hex code) | e.g., `#FFFFFF`, `#EEEEE5`, `#000000` | transparent |
| `shadow` | string | Type of shadow to apply | `soft`, `natural` | none |
| `position` | string | Position of the subject in the output image | `center` | center |
| `scale` | string | Scale of the subject as percentage | e.g., `13` (for 13%) | 100 |
| `size` | string | Predefined size for e-commerce platforms | `portrait`, `square` | original |
| `crop` | string | Whether to automatically crop the image | `true`, `false` | `false` |
| `quality` | string | Output image quality (1-100) | e.g., `50`, `90`, `100` | 90 |
| `width` | string | Custom width in pixels | e.g., `800` | original |
| `height` | string | Custom height in pixels | e.g., `600` | original |
| `bg_blur` | string | Background blur radius in pixels | e.g., `10` | 0 |

### Advanced Parameters (Plus Plan Only)

| Parameter | Type | Description | Possible Values | Default |
|-----------|------|-------------|-----------------|---------|
| `hd` | string | Enable HD background removal | `true`, `false` | `false` |
| `dpi` | string | Pixel density (DPI) | e.g., `300` | 72 |
| `bg_image` | file | Custom background image | Image file | none |
| `bg_image_url` | string | URL of custom background image | Valid URL | none |
| `bg_prompt` | string | Text prompt for AI-generated background | Text description | none |
| `bg_style` | string | Style for AI-generated background | `photographic`, `flat_color`, `gradient`, `pattern` | `photographic` |
| `relight` | string | Apply AI relighting | `true`, `false` | `false` |
| `relight_direction` | string | Direction of the light source | `front`, `left`, `right`, `top` | `front` |
| `relight_strength` | string | Strength of the relighting effect | `low`, `medium`, `high` | `medium` |
| `remove_text` | string | Remove text from image | `true`, `false` | `false` |
| `expand` | string | Expand image canvas | `true`, `false` | `false` |
| `expand_factor` | string | Factor by which to expand the canvas | e.g., `1.5` | 1.2 |
| `upscale` | string | AI upscale image (Alpha) | `true`, `false` | `false` |
| `upscale_factor` | string | Factor by which to upscale | `2`, `4` | 2 |
| `text_prompt` | string | Text-guided segmentation (Alpha) | Text description | none |
| `green_screen_despill` | string | Remove green color spill | `true`, `false` | `false` |

## Parameter Combinations

### Basic Background Removal

For basic background removal with a transparent background, don't specify any additional parameters:

```
POST /v1/segment
```

### Different Output Formats

#### PNG (with transparency)

```
format=png
```

#### JPG (no transparency)

```
format=jpg
```

#### WebP (good compression, supports transparency)

```
format=webp
```

### Background Colors

#### White Background

```
bg_color=#FFFFFF
format=webp
```

#### Light Beige Background (#EEEEE5)

```
bg_color=#EEEEE5
format=webp
```

#### Black Background

```
bg_color=#000000
format=webp
```

### Shadows

#### Soft AI Shadow

```
bg_color=#EEEEE5
shadow=soft
format=webp
```

#### Natural Shadow

```
bg_color=#EEEEE5
shadow=natural
format=webp
```

### Positioning and Scaling

#### Center Position

```
bg_color=#EEEEE5
shadow=soft
position=center
format=webp
```

#### 13% Scaling

```
bg_color=#EEEEE5
shadow=soft
position=center
scale=13
format=webp
```

### E-commerce Sizes

#### Shopify Portrait Size (4:5 ratio)

```
bg_color=#EEEEE5
shadow=soft
position=center
scale=13
size=portrait
format=webp
```

#### Shopify Square Size (1:1 ratio)

```
bg_color=#EEEEE5
shadow=soft
position=center
scale=13
size=square
format=webp
```

### Cropping

#### Portrait with Auto Crop

```
bg_color=#EEEEE5
shadow=soft
position=center
scale=13
size=portrait
crop=true
format=webp
```

#### Square with Auto Crop

```
bg_color=#EEEEE5
shadow=soft
position=center
scale=13
size=square
crop=true
format=webp
```

### Quality Settings

#### High Quality (100%)

```
bg_color=#EEEEE5
shadow=soft
position=center
scale=13
size=portrait
crop=true
format=webp
quality=100
```

#### Low Quality (50%)

```
bg_color=#EEEEE5
shadow=soft
position=center
scale=13
size=portrait
crop=true
format=webp
quality=50
```

### Custom Sizing

```
bg_color=#EEEEE5
shadow=soft
position=center
width=800
height=600
format=webp
```

### Background Effects

#### Background Blur

```
bg_blur=10
format=webp
```

### Plus Plan Features

#### HD Background Removal

```
hd=true
format=webp
```

#### Custom DPI Setting

```
dpi=300
format=webp
```

#### AI-Generated Background

```
bg_prompt=A beautiful beach at sunset
bg_style=photographic
format=webp
```

#### AI Relighting

```
relight=true
relight_direction=left
relight_strength=medium
format=webp
```

#### Text Removal

```
remove_text=true
format=webp
```

#### Image Expansion

```
expand=true
expand_factor=1.5
format=webp
```

#### AI Upscale (Alpha)

```
upscale=true
upscale_factor=2
format=webp
```

#### Text-Guided Segmentation (Alpha)

```
text_prompt=a person in a red shirt
format=webp
```

### Optimized for Shopify

```
bg_color=#EEEEE5
shadow=soft
position=center
scale=13
size=portrait
crop=true
format=webp
quality=90
```

## Response Headers

The API response includes useful information in the headers:

- `x-uncertainty-score`: Confidence score of the segmentation
- `x-foreground-top`: Top position of the foreground subject
- `x-foreground-left`: Left position of the foreground subject
- `x-foreground-height`: Height of the foreground subject
- `x-foreground-width`: Width of the foreground subject

## Error Codes

- `402`: API limit reached
- `4xx`: Client errors (invalid parameters, authentication issues)
- `5xx`: Server errors

## Notes

- The API has rate limits. For high-volume processing, consider batch processing with appropriate delays.
- For testing purposes, you can use the sandbox API key (prefix your API key with "sandbox_").
- The maximum recommended input image size is 1000x1000 pixels for optimal performance.
- The Plus plan offers more advanced features like AI backgrounds, relighting, and text removal.
- Some features are in Alpha stage and may not be fully stable.
- The Image Editing API v2 (Plus plan) offers more capabilities than v1. 