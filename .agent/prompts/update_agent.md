When implementing or modifying a feature:

1. Identify affected modules and layers

2. Keep responsibilities clean:

    * imports handles PDF ingestion/parsing
    * tracking handles meal completion, notes, and meal image attachments
    * ai handles OpenRouter integration

3. Update, where relevant:

    * architecture.md
    * roadmap.md
    * tasks/current_tasks.md
    * agent_context.md

4. Ensure responsive/mobile-first behavior remains intact

5. Keep implementation incremental and modular

6. After implementation, document:

    * what changed
    * remaining TODOs
    * follow-up steps
