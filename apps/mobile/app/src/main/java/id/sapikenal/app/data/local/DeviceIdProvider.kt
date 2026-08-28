package id.sapikenal.app.data.local

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/** Provides a stable app-scoped identifier without reading hardware identifiers. */
@Singleton
class DeviceIdProvider
    @Inject
    constructor(
        @ApplicationContext context: Context,
    ) {
        private val preferences = context.getSharedPreferences(PREFERENCES_NAME, Context.MODE_PRIVATE)

        val value: String by lazy {
            preferences.getString(KEY_DEVICE_ID, null)
                ?: UUID.randomUUID().toString().also { generated ->
                    preferences.edit().putString(KEY_DEVICE_ID, generated).apply()
                }
        }

        private companion object {
            const val PREFERENCES_NAME = "device_identity"
            const val KEY_DEVICE_ID = "device_id"
        }
    }
