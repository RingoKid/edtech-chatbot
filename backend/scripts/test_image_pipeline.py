"""
Manual test script: invoke image director LLM + Gemini image generation.

Runs the full image pipeline in isolation:
1. Calls gpt-4o with structured output → ImagePlan (3 prompts)
2. Generates 3 images via Gemini 2.5 Flash (saves locally)
3. Optionally uploads to S3

Usage:
    docker compose exec backend python scripts/test_image_pipeline.py
    docker compose exec backend python scripts/test_image_pipeline.py --skip-s3
"""

import asyncio
import sys
import time
import os
import argparse

# -----------------------------------------------------------
# Args
# -----------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--skip-s3", action="store_true", help="Skip S3 upload step")
parser.add_argument("--skip-gemini", action="store_true", help="Skip Gemini generation, test LLM only")
args = parser.parse_args()

# -----------------------------------------------------------
# Step 0: Verify env vars
# -----------------------------------------------------------
missing = []
for var in ["OPENAI_API_KEY", "GEMINI_API_KEY"]:
    if not os.environ.get(var):
        missing.append(var)
if missing:
    print(f"❌ Missing env vars: {', '.join(missing)}")
    sys.exit(1)

print("✅ Environment variables present")

# -----------------------------------------------------------
# Step 1: Image Director — gpt-4o structured output → ImagePlan
# -----------------------------------------------------------
from app.llm.client import get_chat_model
from app.schemas.image import ImagePlan
from app.graph.nodes.image_director import (
    IMAGE_DIRECTOR_SYSTEM_PROMPT,
    USER_MESSAGE_TEMPLATE,
)

SAMPLE_LESSON = """\
# Handwriting Lesson: Uppercase Letter D (Kindergarten, On-Level)

## Review & Connect
Today we'll learn to write the uppercase letter D! Let's start by reviewing \
the letter C that we learned last time. Can you trace a big C in the air?

## Model, Explain & Engage
Watch me write the letter D. First, I draw a tall straight line going down \
from top to bottom. Then I go back to the top and draw a big curve that goes \
to the right and comes back down to meet the bottom of my straight line.

### Stroke Order
1. Start at the top left — draw a vertical line straight down to the baseline.
2. Go back to the top — draw a curved line from top to bottom (like a big belly).

## Guided Practice
Now it's your turn! Put your finger on the green dot and trace the letter D. \
Remember: straight line down first, then the big belly curve.

## Application
Can you find things in our classroom that start with the /d/ sound? A desk, \
a door, a doll! Now write the letter D three times on your paper.
"""


def test_image_director_llm():
    """Call gpt-4o with structured output and validate the ImagePlan."""
    print("\n" + "=" * 60)
    print("STEP 1: Image Director LLM (gpt-4o → ImagePlan)")
    print("=" * 60)

    model = get_chat_model("gpt-4o")
    structured_model = model.with_structured_output(ImagePlan)

    user_message = USER_MESSAGE_TEMPLATE.format(
        grade="K",
        letter="D",
        student_level="on-level",
        lesson_markdown=SAMPLE_LESSON,
    )

    print(f"Calling gpt-4o with structured output...")
    t0 = time.time()

    try:
        image_plan: ImagePlan = structured_model.invoke([
            {"role": "system", "content": IMAGE_DIRECTOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ])
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return None

    elapsed = time.time() - t0
    print(f"✅ LLM call succeeded in {elapsed:.1f}s")
    print(f"   Images planned: {len(image_plan.images)}")

    for i, img in enumerate(image_plan.images, 1):
        print(f"\n   Image {i}:")
        print(f"   Placement:  {img.placement}")
        print(f"   Alt text:   {img.alt_text}")
        print(f"   Role:       {img.pedagogical_role}")
        print(f"   Prompt:     {img.prompt[:120]}...")

    return image_plan


# -----------------------------------------------------------
# Step 2: Gemini image generation (local save, no S3)
# -----------------------------------------------------------
from app.services.image_service import (
    generate_image,
    image_to_jpeg_bytes,
    PROMPT_PREFIX,
)


def test_gemini_generation_local(image_plan: ImagePlan):
    """Generate 3 images via Gemini and save locally."""
    print("\n" + "=" * 60)
    print("STEP 2: Gemini Image Generation (local)")
    print("=" * 60)

    os.makedirs("/tmp/test-images", exist_ok=True)
    results = []

    for i, img in enumerate(image_plan.images, 1):
        print(f"\n   Generating image {i}/3...")
        t0 = time.time()
        try:
            pil_image = generate_image(img.prompt)
            jpeg_bytes = image_to_jpeg_bytes(pil_image)
            path = f"/tmp/test-images/img_{i}.jpg"
            with open(path, "wb") as f:
                f.write(jpeg_bytes)
            elapsed = time.time() - t0
            print(f"   ✅ Image {i} generated in {elapsed:.1f}s")
            print(f"      Size: {len(jpeg_bytes):,} bytes")
            print(f"      Mode: {pil_image.mode}, Dimensions: {pil_image.size}")
            print(f"      Saved: {path}")
            results.append({"path": path, "bytes": len(jpeg_bytes)})
        except Exception as e:
            elapsed = time.time() - t0
            print(f"   ❌ Image {i} failed in {elapsed:.1f}s: {e}")
            results.append(None)

    success_count = sum(1 for r in results if r is not None)
    print(f"\n   {success_count}/3 images generated successfully")
    return results


# -----------------------------------------------------------
# Step 3: S3 upload (optional)
# -----------------------------------------------------------
from app.services.image_service import upload_to_s3, compute_s3_key


def test_s3_upload(image_results: list, thread_id: str):
    """Upload generated images to S3."""
    print("\n" + "=" * 60)
    print("STEP 3: S3 Upload")
    print("=" * 60)

    for i, result in enumerate(image_results, 1):
        if result is None:
            print(f"   ⏭  Skipping image {i} (not generated)")
            continue

        s3_key = compute_s3_key(thread_id, i)
        print(f"   Uploading image {i} to s3://{s3_key}...")
        try:
            with open(result["path"], "rb") as f:
                jpeg_bytes = f.read()
            url = upload_to_s3(jpeg_bytes, s3_key)
            print(f"   ✅ Uploaded: {url}")
        except Exception as e:
            print(f"   ❌ Upload failed: {e}")


# -----------------------------------------------------------
# Main
# -----------------------------------------------------------
def main():
    print("🔬 Image Pipeline Manual Test")
    print(f"   Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: LLM planning
    image_plan = test_image_director_llm()
    if image_plan is None:
        print("\n❌ FAILED at Step 1 — LLM planning")
        sys.exit(1)

    if args.skip_gemini:
        print("\n⏭  Skipping Gemini generation (--skip-gemini)")
        print("\n✅ STEP 1 PASSED — LLM planning works")
        sys.exit(0)

    # Step 2: Gemini generation (local)
    image_results = test_gemini_generation_local(image_plan)
    success_count = sum(1 for r in image_results if r is not None)
    if success_count == 0:
        print("\n❌ FAILED at Step 2 — No images generated")
        sys.exit(1)

    # Step 3: S3 upload (optional)
    if not args.skip_s3:
        thread_id = f"test-pipeline-{int(time.time())}"
        test_s3_upload(image_results, thread_id)
    else:
        print("\n⏭  Skipping S3 upload (--skip-s3)")

    # Summary
    print("\n" + "=" * 60)
    print(f"✅ PIPELINE TEST COMPLETE ({success_count}/3 images)")
    print("=" * 60)


if __name__ == "__main__":
    main()
