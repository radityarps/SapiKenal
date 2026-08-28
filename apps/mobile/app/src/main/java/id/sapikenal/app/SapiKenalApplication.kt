package id.sapikenal.app

import android.app.Application
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import dagger.hilt.android.HiltAndroidApp
import id.sapikenal.app.data.repository.PurgeManager
import id.sapikenal.app.data.sync.HistorySyncScheduler
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltAndroidApp
class SapiKenalApplication :
    Application(),
    Configuration.Provider {
    @Inject lateinit var purgeManager: PurgeManager

    @Inject lateinit var workerFactory: HiltWorkerFactory

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder().setWorkerFactory(workerFactory).build()

    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        // Purge soft-deleted records older than 30 days on each app launch
        applicationScope.launch {
            runCatching { purgeManager.purgeExpired() }
            HistorySyncScheduler.enqueue(this@SapiKenalApplication)
        }
    }
}
