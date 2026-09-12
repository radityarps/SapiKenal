package id.sapikenal.app.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Singleton

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

@Singleton
class SettingsDataStore(
    @ApplicationContext private val context: Context,
) {
    companion object Keys {
        val KEY_LANGUAGE = stringPreferencesKey("language")
        val KEY_TEXT_SIZE = stringPreferencesKey("text_size")
        val KEY_UPLOAD_CONSENT = booleanPreferencesKey("upload_consent")
    }

    val language: Flow<String> =
        context.dataStore.data.map { prefs ->
            prefs[KEY_LANGUAGE] ?: "system"
        }

    val textSize: Flow<String> =
        context.dataStore.data.map { prefs ->
            prefs[KEY_TEXT_SIZE] ?: "system"
        }

    suspend fun setLanguage(value: String) {
        context.dataStore.edit { prefs -> prefs[KEY_LANGUAGE] = value }
    }

    suspend fun setTextSize(value: String) {
        context.dataStore.edit { prefs -> prefs[KEY_TEXT_SIZE] = value }
    }

    val uploadConsent: Flow<Boolean?> =
        context.dataStore.data.map { prefs ->
            if (prefs.contains(KEY_UPLOAD_CONSENT)) prefs[KEY_UPLOAD_CONSENT] else null
        }

    suspend fun setUploadConsent(value: Boolean) {
        context.dataStore.edit { prefs -> prefs[KEY_UPLOAD_CONSENT] = value }
    }
}
