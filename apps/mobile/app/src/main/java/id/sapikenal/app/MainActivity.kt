package id.sapikenal.app

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dagger.hilt.android.AndroidEntryPoint
import id.sapikenal.app.data.local.SettingsDataStore
import id.sapikenal.app.data.local.dataStore
import id.sapikenal.app.ui.navigation.SapiKenalNavHost
import id.sapikenal.app.ui.theme.SapiKenalTheme
import id.sapikenal.app.utils.LocaleManager
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        val savedLanguage =
            runBlocking {
                applicationContext.dataStore.data
                    .map { prefs -> prefs[SettingsDataStore.KEY_LANGUAGE] ?: "system" }
                    .first()
            }
        LocaleManager.applyLanguage(savedLanguage)

        super.onCreate(savedInstanceState)

        enableEdgeToEdge()
        setContent {
            val textSizeMode by applicationContext.dataStore.data
                .map { prefs -> prefs[SettingsDataStore.KEY_TEXT_SIZE] ?: "system" }
                .collectAsStateWithLifecycle(initialValue = "system")

            SapiKenalTheme(textSizeMode = textSizeMode) {
                SapiKenalNavHost()
            }
        }
    }
}
