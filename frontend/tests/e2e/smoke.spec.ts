import { expect, test } from "@playwright/test";

import { installMockApi } from "./mock-api";

test("dashboard page loads with the core workspace overview", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Research workspace" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "All workflow modules are live" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /Search Papers Discover literature/i }),
  ).toBeVisible();
  await expect(page.getByText("Three steps to a grounded research answer.")).toBeVisible();
});

test("happy-path smoke flow covers search, ingest, index, chat, compare, and synthesis", async ({
  page,
}) => {
  const recordedCalls = await installMockApi(page);

  await test.step("Search page renders and submits a mocked search", async () => {
    await page.goto("/search");

    await expect(
      page.getByText("Search arXiv by topic and inspect normalized paper metadata."),
    ).toBeVisible();

    await page.getByLabel("Topic query").fill("vision transformer medical imaging");
    await page.getByRole("button", { name: "Search arXiv" }).click();

    await expect(
      page.getByRole("heading", { name: "Vision Transformers for Medical Imaging" }),
    ).toBeVisible();
    await expect(
      page.getByText('1 paper for "vision transformer medical imaging"'),
    ).toBeVisible();
  });

  await test.step("Search results can ingest and index a paper", async () => {
    await page
      .getByRole("button", { name: "Ingest Vision Transformers for Medical Imaging" })
      .click();

    await expect(
      page.getByText("Paper ingested and parsed successfully. 12 pages | 4,321 words."),
    ).toBeVisible();

    await page
      .getByRole("button", { name: "Index Vision Transformers for Medical Imaging" })
      .click();

    await expect(page.getByText("Indexed 42 chunks into paper_chunks.")).toBeVisible();
    await expect(page.getByText("Indexed", { exact: true })).toBeVisible();
  });

  await test.step("Chat page renders grounded answers with citation and evidence panels", async () => {
    await page.goto("/chat");

    await expect(page.getByText("Ask research questions over indexed papers.")).toBeVisible();

    await page
      .getByLabel("Research question")
      .fill("What limitations are reported for these models?");
    await page.getByLabel("Restrict to paper IDs (optional)").fill("2401.12345");
    await page.getByRole("button", { name: "Ask grounded question" }).click();

    await expect(
      page.getByText("Small-data performance remains fragile, and training can be memory-intensive."),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Trace the answer back to paper pages." }),
    ).toBeVisible();
    await expect(
      page.getByText("Grounded evidence: limited labeled data makes performance unstable."),
    ).toBeVisible();
    await expect(page.getByText("2 chunks in the grounded context package")).toBeVisible();
  });

  await test.step("Compare page renders structured results and synthesis output", async () => {
    await page.goto("/compare");

    await expect(
      page.getByText("Compare indexed papers and synthesize a grounded topic overview."),
    ).toBeVisible();

    await page.getByLabel("Paper IDs (2 to 5)").fill("2401.12345, 2402.67890");
    await page.locator('textarea[name="question"]').fill("Compare methodology and datasets.");
    await page.getByRole("button", { name: "Compare indexed papers" }).click();

    await expect(page.getByText("Grounded comparison summary.")).toBeVisible();
    await expect(page.getByRole("cell", { name: "EyePACS" })).toBeVisible();
    await expect(page.getByRole("cell", { name: "ChestX-ray14" })).toBeVisible();
    await expect(page.getByText("2 chunks in the comparison package")).toBeVisible();

    await page
      .getByLabel("Topic (optional if paper IDs are provided)")
      .fill("Vision transformers in medical imaging");
    await page
      .getByLabel("Restrict to paper IDs (optional)")
      .fill("2401.12345, 2402.67890");
    await page.getByRole("button", { name: "Generate topic synthesis" }).click();

    await expect(
      page.getByRole("heading", { name: "Vision transformers in medical imaging" }),
    ).toBeVisible();
    await expect(
      page.getByText(
        "Transformer backbones are increasingly paired with hybrid designs to balance capacity and data efficiency.",
      ),
    ).toBeVisible();
    await expect(page.getByText("Transformer-based feature extraction")).toBeVisible();
    await expect(page.getByText("Small labeled datasets remain a bottleneck.")).toBeVisible();
    await expect(page.getByText("2 chunks in the synthesis package")).toBeVisible();
  });

  expect(recordedCalls).toEqual([
    {
      path: "/api/search-papers",
      body: { query: "vision transformer medical imaging", max_results: 10 },
    },
    {
      path: "/api/ingest",
      body: {
        id: "2401.12345",
        title: "Vision Transformers for Medical Imaging",
        authors: ["Alice Smith", "Bob Jones"],
        abstract:
          "Grounded benchmark study showing transformer trade-offs in medical image analysis.",
        published_at: "2024-01-10T12:00:00Z",
        updated_at: "2024-01-15T09:30:00Z",
        categories: ["cs.CV", "cs.LG"],
        pdf_url: "https://arxiv.org/pdf/2401.12345.pdf",
        source_url: "https://arxiv.org/abs/2401.12345",
        primary_category: "cs.CV",
      },
    },
    {
      path: "/api/index-paper",
      body: { paper_id: "2401.12345" },
    },
    {
      path: "/api/chat",
      body: {
        question: "What limitations are reported for these models?",
        paper_ids: ["2401.12345"],
        top_k: 6,
      },
    },
    {
      path: "/api/compare",
      body: {
        paper_ids: ["2401.12345", "2402.67890"],
        question: "Compare methodology and datasets.",
      },
    },
    {
      path: "/api/summarize-topic",
      body: {
        topic: "Vision transformers in medical imaging",
        paper_ids: ["2401.12345", "2402.67890"],
      },
    },
  ]);
});
