# ANIMA Prompt Engineering Guide

This guide details official best practices, syntax rules, structural principles, and optimization workflows for prompting with the **ANIMA** AI model.

---

## 1. What is the ANIMA AI Model?

**ANIMA** is a next-generation anime and illustrative image generation model developed by **CircleStone Labs** in collaboration with **Comfy Org**.

Unlike legacy Stable Diffusion models that use CLIP text encoders, ANIMA is built around a **Qwen text encoder** architecture (based on Qwen2.5 8B LLM). This enables ANIMA to possess deep semantic comprehension, complex instruction following, and seamless handling of both structured tags and natural language narrative descriptions.

---

## 2. Core Prompting Strategy: Hybrid Prompting

The optimal prompting strategy for ANIMA is **Hybrid Prompting**: combining Danbooru-style anime tags for precise visual traits with natural language sentences for dynamic composition, lighting, and narrative context.

### Structural Order
1. **Quality Score & Safety Anchors**: e.g., `score_9, score_8, score_7, masterpiece, best quality`
2. **Artist Anchors**: e.g., `@artist_name`
3. **Subject & Character Features**: Character identity, hair color, eye color, expression
4. **Attire & Poses**: Clothing items, accessories, pose, action
5. **Environment & Background**: Location, props, ambient setting
6. **Lighting, Mood & Optics**: Natural language lighting, color palette, camera angle

---

## 3. Syntax Rules & Formatting Guidelines

### 🚫 1. No SD Weight Multipliers
- **Rule**: Do **NOT** use SD-style weight syntax such as `(tag:1.3)`, `(tag:0.8)`, `((tag))`, or `[tag]`.
- **Reasoning**: The Qwen text encoder interprets parentheses as literal text or phrasing punctuation rather than numerical attention weights. SD weight syntax degrades prompt quality and confuses the text encoder.
- **Comparison**:
  - ❌ *Incorrect*: `((masterpiece)), (blue eyes:1.2), (glowing background:0.9)`
  - ✅ *Correct*: `score_9, score_8, score_7, vibrant blue eyes, glowing ethereal background`

### 🎨 2. Artist Syntax Formatting (`@artist_name`)
- **Rule**: Format artist visual style triggers using `@artist_name` syntax.
- **Comparison**:
  - ❌ *Incorrect*: `by artist_name` or `artist:shinkai_makoto`
  - ✅ *Correct*: `@shinkai_makoto`, `@artgem`

### ⭐ 3. Quality Score Anchors
- **Rule**: ANIMA uses score-based quality anchors to position generation along the fine-tuning aesthetic distribution.
- **Positive Score Anchors**: `score_9`, `score_8`, `score_7`, `masterpiece`, `best quality`, `safe`.
- **Placement**: Place quality score anchors at the very beginning of the prompt.

### 🛑 4. Negative Prompt Defaults
- **Rule**: ANIMA uses negative quality score anchors (`score_1`, `score_2`, `score_3`) along with artifact tags to prevent visual degradation.
- **Default Negative Prompt**:
  ```text
  worst quality, low quality, score_1, score_2, score_3, artist name, blurry, bad anatomy, extra fingers
  ```

---

## 4. ANIMA Studio Panel & Optimization Variants

Wildcard Prompt Studio features a dedicated **ANIMA Studio Panel** designed specifically for ANIMA prompt engineering.

### Preset Optimization Variants:
1. ✨ **Hybrid (Recommended)**: Combines Danbooru tags for precise character features with natural language prose for background and lighting.
2. 🏷️ **Tag Focused**: Pure comma-separated anime tag structure for classic anime image generation.
3. 📝 **Natural Language**: Descriptive narrative prose optimized for cinematic and painterly compositions.

---

## 5. Studio Panel Features & Controls

The ANIMA Studio Panel in Wildcard Prompt Studio provides the following tools:

- **Clean SD Weights Toggle / 🧹 Button**: One-click utility that strips legacy SD weight brackets `(tag:1.2)` and `((tag))` from your prompt.
- **Quality Score Injector**: Automatically prepends `score_9, score_8, score_7` if missing from your prompt.
- **Negative Prompt Preset Manager**: Customizable negative prompt generator pre-populated with optimal ANIMA negative score defaults.
- **Real-Time Diff Viewer**: Visual side-by-side comparison showing raw input prompt versus the AI-improved ANIMA prompt.
- **Quick Action Workflow Dispatch**:
  - **Copy Prompt**: Instant clipboard copy.
  - **Send to Prompt Editor**: Send improved prompt directly to the main prompt editor.
  - **Dispatch to ComfyUI**: Send prompt straight into the ComfyUI live stream workflow execution engine.
