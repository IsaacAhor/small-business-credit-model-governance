# Select a review target

The maintainer uses this page before sending a new invitation. A recipient
starts with the selected [review packet](README.md). If a review is already
agreed, continue with its recorded source and instructions.

1. Open the [latest published release](https://github.com/IsaacAhor/small-business-credit-model-governance/releases/latest).
2. If it is **v0.12.0**, use the [preserved v0.12.0 target sheet](targets/v0.12.0.md).
   That release predates the Review target link in release notes.
   For a later release, open the **Review target** link in its notes to reach
   the matching sheet in the tagged source.
3. Select the [technical](technical-review.md),
   [credit governance and adverse-action](practitioner-assessment.md), or
   [methodology](methodology-assessment.md) packet. Confirm that its stated
   source, excerpts, commands, expected observations, and known issues match
   the chosen target. The packets currently describe **v0.12.0**; do not use
   their examples or results as evidence for a later source.
4. Send the chosen packet directly using its commit-pinned URL. Agree and
   record the exact software source, packet and companion instruction revisions,
   scope, effort cap, and return method before starting. Packet links to the
   protocol and target sheet use the packet revision unless otherwise recorded.

If a later release lacks a Review target link, ask the maintainer to resolve
the missing instructions before starting. Do not substitute another version's
sheet or assume that a newer release has corrected earlier findings. A newer
target also needs a checked matching packet. If one is missing, resolve that
gap before inviting a review of it. An older baseline may be reviewed only as
an explicitly agreed older target, with its original limitations retained.

## Earlier release

The v0.12.0 sheet and review instructions were added after the software release.
Its release archive is unchanged, and its disclosed limitations remain part
of the assignment.

## Reviews already agreed

The latest-release link follows the release GitHub marks **Latest**. It does
not change an agreed review or rewrite a historical target sheet. A switch or
retest requires a separate agreement under the
[target-change procedure](protocol.md#changing-the-review-target).
Preserve original results, unresolved findings, and historical links.

Maintainers prepare and verify each future target sheet and its release-note
link under the [release procedure](../release-strategy.md#review-target-routing).
The automated check verifies the sheet's presence, version heading, and link;
it does not verify technical correctness or constitute an external assessment.
