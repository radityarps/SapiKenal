package id.sapikenal.app.ui.result

import com.squareup.moshi.Moshi
import com.squareup.moshi.Types
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import id.sapikenal.app.data.remote.dto.ContentBlockDto

data class ParsedBreedProfile(
    val summaryText: String,
    val strengths: List<String> = emptyList(),
    val limitations: List<String> = emptyList(),
    val rawRemainingBody: String? = null,
    val disclaimer: String? = null,
)

object BreedProfileParser {
    private val blocksAdapter by lazy {
        val listType = Types.newParameterizedType(List::class.java, ContentBlockDto::class.java)
        Moshi.Builder()
            .add(KotlinJsonAdapterFactory())
            .build()
            .adapter<List<ContentBlockDto>>(listType)
    }

    fun parse(
        body: String,
        fallbackSummary: String = "",
        contentBlocksJson: String? = null,
    ): ParsedBreedProfile {
        if (!contentBlocksJson.isNullOrBlank()) {
            val fromBlocks = parseFromBlocks(contentBlocksJson, fallbackSummary)
            if (fromBlocks != null) {
                return fromBlocks
            }
        }
        return parseFromMarkdown(body, fallbackSummary)
    }

    fun parseFromBlocks(
        blocksJson: String,
        fallbackSummary: String = "",
    ): ParsedBreedProfile? =
        runCatching {
            val blocks = blocksAdapter.fromJson(blocksJson) ?: return null
            if (blocks.isEmpty()) return null

            var currentSection = ""
            val summaryLines = mutableListOf<String>()
            val strengths = mutableListOf<String>()
            val limitations = mutableListOf<String>()
            val remainingLines = mutableListOf<String>()
            var disclaimer: String? = null

            for (block in blocks) {
                val content = block.content.trim()
                val items = (block.items ?: emptyList()).map { it.trim() }.filter { it.isNotBlank() }

                if (block.type == "disclaimer" ||
                    content.contains("bukan bukti silsilah", ignoreCase = true) ||
                    content.contains("rekomendasi mutlak", ignoreCase = true)
                ) {
                    if (content.isNotBlank()) {
                        disclaimer = content
                    }
                    continue
                }

                if (block.type == "heading") {
                    val headerMatch = matchesHeader(content)
                    if (headerMatch != null) {
                        currentSection = headerMatch.type
                        if (!headerMatch.inlineContent.isNullOrBlank()) {
                            when (currentSection) {
                                "summary" -> summaryLines.add(headerMatch.inlineContent)
                                "strengths" -> {
                                    val clean = cleanBullet(headerMatch.inlineContent)
                                    if (clean.isNotBlank()) strengths.add(clean)
                                }
                                "limitations" -> {
                                    val clean = cleanBullet(headerMatch.inlineContent)
                                    if (clean.isNotBlank()) limitations.add(clean)
                                }
                            }
                        }
                    } else {
                        currentSection = "other"
                        if (content.isNotBlank()) {
                            remainingLines.add(content)
                        }
                    }
                    continue
                }

                if (block.type == "bullet_list") {
                    when (currentSection) {
                        "strengths" -> strengths.addAll(items)
                        "limitations" -> limitations.addAll(items)
                        "summary" -> summaryLines.addAll(items)
                        else -> {
                            items.forEach { remainingLines.add("• $it") }
                        }
                    }
                    continue
                }

                if (content.isNotBlank()) {
                    when (currentSection) {
                        "summary" -> summaryLines.add(content)
                        "strengths" -> {
                            val clean = cleanBullet(content)
                            if (clean.isNotBlank()) strengths.add(clean)
                        }
                        "limitations" -> {
                            val clean = cleanBullet(content)
                            if (clean.isNotBlank()) limitations.add(clean)
                        }
                        else -> {
                            if (summaryLines.isEmpty()) {
                                summaryLines.add(content)
                            } else {
                                remainingLines.add(content)
                            }
                        }
                    }
                }
            }

            val summaryText =
                if (summaryLines.isNotEmpty()) {
                    summaryLines.joinToString(" ")
                } else {
                    fallbackSummary.trim()
                }

            ParsedBreedProfile(
                summaryText = summaryText,
                strengths = strengths,
                limitations = limitations,
                rawRemainingBody = remainingLines.takeIf { it.isNotEmpty() }?.joinToString("\n"),
                disclaimer = disclaimer,
            )
        }.getOrNull()

    fun parseFromMarkdown(
        body: String,
        fallbackSummary: String = "",
    ): ParsedBreedProfile {
        val trimmedBody = body.trim()
        if (trimmedBody.isBlank()) {
            return ParsedBreedProfile(summaryText = fallbackSummary.trim())
        }

        val lines = trimmedBody.lines().map { it.trim() }

        var currentSection = ""
        val summaryLines = mutableListOf<String>()
        val strengths = mutableListOf<String>()
        val limitations = mutableListOf<String>()
        val remainingLines = mutableListOf<String>()
        var disclaimer: String? = null
        var hasKnownHeaders = false

        for (line in lines) {
            if (line.isBlank()) continue

            // Detect disclaimer note
            if (line.contains("bukan bukti silsilah", ignoreCase = true) ||
                line.contains("rekomendasi mutlak", ignoreCase = true)
            ) {
                disclaimer = line
                continue
            }

            val isBullet = line.startsWith("•") || line.startsWith("-") || line.startsWith("*")

            if (!isBullet) {
                val headerMatch = matchesHeader(line)
                if (headerMatch != null) {
                    hasKnownHeaders = true
                    currentSection = headerMatch.type
                    if (!headerMatch.inlineContent.isNullOrBlank()) {
                        when (currentSection) {
                            "summary" -> summaryLines.add(headerMatch.inlineContent)
                            "strengths" -> {
                                val clean = cleanBullet(headerMatch.inlineContent)
                                if (clean.isNotBlank()) strengths.add(clean)
                            }
                            "limitations" -> {
                                val clean = cleanBullet(headerMatch.inlineContent)
                                if (clean.isNotBlank()) limitations.add(clean)
                            }
                        }
                    }
                    continue
                }
            }

            when (currentSection) {
                "summary" -> summaryLines.add(line)
                "strengths" -> {
                    val clean = cleanBullet(line)
                    if (clean.isNotBlank()) strengths.add(clean)
                }
                "limitations" -> {
                    val clean = cleanBullet(line)
                    if (clean.isNotBlank()) limitations.add(clean)
                }
                else -> {
                    if (hasKnownHeaders) {
                        remainingLines.add(line)
                    } else {
                        // Unstructured body fallback
                        if (summaryLines.isEmpty() && !isBullet) {
                            summaryLines.add(line)
                        } else if (isBullet) {
                            val clean = cleanBullet(line)
                            if (clean.isNotBlank()) strengths.add(clean)
                        } else {
                            remainingLines.add(line)
                        }
                    }
                }
            }
        }

        val summaryText =
            if (summaryLines.isNotEmpty()) {
                summaryLines.joinToString(" ")
            } else {
                fallbackSummary.trim().ifBlank { trimmedBody.take(250) }
            }

        return ParsedBreedProfile(
            summaryText = summaryText,
            strengths = strengths,
            limitations = limitations,
            rawRemainingBody = remainingLines.takeIf { it.isNotEmpty() }?.joinToString("\n"),
            disclaimer = disclaimer,
        )
    }

    private data class HeaderMatchResult(
        val type: String,
        val inlineContent: String? = null,
    )

    private fun matchesHeader(line: String): HeaderMatchResult? {
        val colonIndex = line.indexOf(':')
        val headerCandidate = (if (colonIndex != -1) line.substring(0, colonIndex) else line).trim().lowercase()
        val inlineContent = if (colonIndex != -1) line.substring(colonIndex + 1).trim().takeIf { it.isNotBlank() } else null

        val type =
            when {
                headerCandidate == "ringkasan profil" ||
                    headerCandidate == "ringkasan" ||
                    headerCandidate.startsWith("ringkasan") ||
                    headerCandidate == "deskripsi" ||
                    headerCandidate.startsWith("ciri fisik") ||
                    headerCandidate.startsWith("karakteristik") -> "summary"

                headerCandidate == "kelebihan" ||
                    headerCandidate == "kelebiha" ||
                    headerCandidate.startsWith("kelebih") ||
                    headerCandidate == "keunggulan" ||
                    headerCandidate.startsWith("keunggul") ||
                    headerCandidate.startsWith("potensi") -> "strengths"

                headerCandidate == "kekurangan" ||
                    headerCandidate == "kekuranga" ||
                    headerCandidate.startsWith("kekurang") ||
                    headerCandidate.startsWith("kelemah") ||
                    headerCandidate.startsWith("batasan") -> "limitations"

                else -> null
            }

        return type?.let { HeaderMatchResult(it, inlineContent) }
    }

    private fun cleanBullet(line: String): String =
        line
            .removePrefix("•")
            .removePrefix("-")
            .removePrefix("*")
            .trim()
}
