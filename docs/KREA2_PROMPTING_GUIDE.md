# Krea 2 Prompt Engineering Guide

This guide details official best practices, structural principles, and optimization techniques for prompting with **Krea 2** text-to-image models.

---

## 1. Core Principles of Krea 2 Prompting

Unlike legacy Stable Diffusion 1.5/SDXL models that relied heavily on comma-separated tag lists and quality buzzwords, **Krea 2** is built on natural language comprehension and faithfulness-first intent alignment.

### Key Guidelines:
1. **Natural Language Priority**: Express scenes as fluid, coherent descriptive sentences rather than disconnected tags.
2. **Faithfulness First**: Specify key subjects, actions, lighting, and composition explicitly. The model follows direct descriptions accurately without needing artificial weights.
3. **Exact Text Quotation Formatting**: Any text to be rendered visually MUST be enclosed within exact double quotation marks (`"text"`).
4. **Zero Buzzword Pollution**: Avoid generic quality tags like `8k`, `masterpiece`, `ultra-detailed`, or `trending on artstation`. They reduce prompt clarity and degrade visual accuracy.

---

## 2. Krea 2 Model Variant Selection Strategy

Wildcard Prompt Studio V2 provides three optimized variant presets for Krea 2:

### ⚡ 1. Turbo Variant (`turbo`)
- **Target**: Fast generation cycles, rapid prototyping, direct execution.
- **Style**: Concise, punchy natural language. Focuses on subject, lighting, and camera angle.
- **Example**:
  - ❌ *Legacy*: `cyberpunk girl, neon lights, 8k, masterpiece, trending on artstation`
  - ✅ *Krea 2 Turbo*: `A cinematic close-up of a cyberpunk girl with glowing neon implants standing in a rain-slicked city street at night.`

---

### 🎨 2. Medium Variant (`medium`)
- **Target**: Stylized digital art, concept paintings, anime, and expressive illustration styles.
- **Style**: Rich artistic descriptors, color palettes, medium definitions (e.g. oil painting, watercolor, digital concept art).
- **Example**:
  - ✅ *Krea 2 Medium*: `An expressive watercolor painting of a wandering knight standing atop a misty mountain ridge at sunrise, soft pastel gradients, detailed brushwork.`

---

### 📷 3. Large Variant (`large`)
- **Target**: Ultra-photorealism, architectural visualization, dynamic optics, physical texture fidelity.
- **Style**: Camera lens parameters, aperture settings (`f/1.8`), depth-of-field, physical material properties, natural environmental lighting.
- **Example**:
  - ✅ *Krea 2 Large*: `A high-resolution photograph of an elderly craftsman carving wood in a sunlit workshop. Captured on 85mm lens at f/1.8, shallow depth of field, natural window lighting, visible wood grain textures.`

---

## 3. Text Rendering & Quotation Rules

When generating images that include text elements (e.g., street signs, logos, typography, neon lights, t-shirts), Krea 2 uses exact quotation matching:

### Formatting Rules:
- Always wrap the exact words in double quotes: `"YOUR TEXT HERE"`.
- Use the **1-Click Quote Helper** in Krea 2 Studio Panel to automatically detect and format text targets.

### Examples:
- ❌ *Incorrect*: `a coffee shop sign saying Open 24 Hours`
- ✅ *Correct*: `A cozy coffee shop front with a glowing neon sign reading "OPEN 24 HOURS"`

---

## 4. Migrating from Legacy Prompts to Krea 2

| Legacy SD Anti-Pattern | Krea 2 Best Practice |
|---|---|
| `masterpiece, best quality, 8k, hyperdetailed` | Remove entirely; describe subject details and lighting directly instead. |
| `(cyberpunk:1.3), ((neon lights))` | Use natural language phrasing: `illuminated by intense neon lights`. |
| `a woman, portrait, 35mm, highly detailed` | Combine into a complete sentence: `A detailed 35mm portrait photograph of a woman...` |
