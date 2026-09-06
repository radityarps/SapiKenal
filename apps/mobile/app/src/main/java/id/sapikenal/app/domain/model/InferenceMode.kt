package id.sapikenal.app.domain.model

import androidx.annotation.StringRes
import id.sapikenal.app.R

/** The route used to produce an identification result. */
enum class InferenceMode(
    @StringRes val labelResId: Int,
) {
    ONLINE(R.string.result_mode_online),
    OFFLINE(R.string.result_mode_offline),
    OFFLINE_FALLBACK(R.string.result_mode_offline_fallback),
    UNKNOWN(R.string.result_mode_unknown),
    ;

    companion object {
        fun parse(value: String): InferenceMode {
            val normalized = value.trim()
            return entries.firstOrNull { it.name.equals(normalized, ignoreCase = true) } ?: UNKNOWN
        }
    }
}
