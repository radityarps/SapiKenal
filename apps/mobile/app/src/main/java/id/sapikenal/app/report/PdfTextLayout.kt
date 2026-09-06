package id.sapikenal.app.report

/** Pure text measurement helpers used by the Android PDF renderer. */
internal object PdfTextLayout {
    fun wrap(
        text: String,
        maxWidth: Float,
        measureText: (String) -> Float,
    ): List<String> = wrapWithPrefixes(text, maxWidth, measureText)

    fun wrapWithPrefixes(
        text: String,
        maxWidth: Float,
        measureText: (String) -> Float,
        firstPrefix: String = "",
        continuationPrefix: String = "",
    ): List<String> {
        require(maxWidth > 0f) { "maxWidth must be positive" }
        return text
            .split('\n', limit = Int.MAX_VALUE)
            .flatMapIndexed { index, paragraph ->
                wrapParagraph(
                    paragraph,
                    maxWidth,
                    measureText,
                    if (index == 0) firstPrefix else continuationPrefix,
                    continuationPrefix,
                )
            }
    }

    fun fits(
        top: Float,
        height: Float,
        bottom: Float,
    ): Boolean = top >= 0f && height >= 0f && bottom >= top && top + height <= bottom

    fun scaleWithinBounds(
        width: Int,
        height: Int,
        maxWidth: Float,
        maxHeight: Float,
    ): Pair<Int, Int>? {
        if (width <= 0 || height <= 0 || maxWidth <= 0f || maxHeight <= 0f) return null
        val scale = minOf(maxWidth / width, maxHeight / height)
        return (width * scale).toInt().coerceAtLeast(1) to (height * scale).toInt().coerceAtLeast(1)
    }

    private fun wrapParagraph(
        paragraph: String,
        maxWidth: Float,
        measureText: (String) -> Float,
        firstPrefix: String,
        continuationPrefix: String,
    ): List<String> {
        if (paragraph.isBlank()) return listOf(firstPrefix.trimEnd())

        val words = paragraph.trim().split(Regex("\\s+"))
        val result = mutableListOf<String>()
        var prefix = firstPrefix
        var current = ""

        fun flush() {
            if (current.isNotEmpty()) {
                result += prefix + current
                current = ""
                prefix = continuationPrefix
            }
        }

        words.forEach { word ->
            val candidate = if (current.isEmpty()) prefix + word else "$prefix$current $word"
            if (measureText(candidate) <= maxWidth) {
                current = if (current.isEmpty()) word else "$current $word"
                return@forEach
            }

            flush()
            if (measureText(prefix + word) <= maxWidth) {
                current = word
            } else {
                prefix = splitLongWord(word, prefix, continuationPrefix, maxWidth, measureText, result)
            }
        }
        flush()
        return result
    }

    private fun splitLongWord(
        word: String,
        initialPrefix: String,
        continuationPrefix: String,
        maxWidth: Float,
        measureText: (String) -> Float,
        result: MutableList<String>,
    ): String {
        var remaining = word
        var prefix = initialPrefix
        while (remaining.isNotEmpty()) {
            var end = remaining.length
            while (end > 1 && measureText(prefix + remaining.substring(0, end)) > maxWidth) {
                end--
            }
            if (measureText(prefix + remaining.substring(0, end)) > maxWidth) {
                result += prefix + remaining.first()
                end = 1
            } else {
                result += prefix + remaining.substring(0, end)
            }
            remaining = remaining.substring(end)
            prefix = continuationPrefix
        }
        return prefix
    }
}
