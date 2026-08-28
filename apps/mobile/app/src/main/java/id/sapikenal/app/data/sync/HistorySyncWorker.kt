package id.sapikenal.app.data.sync

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.ListenableWorker.Result
import androidx.work.WorkerParameters
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject

@HiltWorker
class HistorySyncWorker
    @AssistedInject
    constructor(
        @Assisted appContext: Context,
        @Assisted workerParams: WorkerParameters,
        private val syncRunner: HistorySyncRunner,
    ) : CoroutineWorker(appContext, workerParams) {
        override suspend fun doWork(): Result =
            when (syncRunner.run()) {
                HistorySyncAttempt.SUCCESS -> Result.success()
                HistorySyncAttempt.RETRY -> Result.retry()
            }
    }
