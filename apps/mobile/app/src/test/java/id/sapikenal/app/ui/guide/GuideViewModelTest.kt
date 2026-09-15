package id.sapikenal.app.ui.guide

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.mockito.kotlin.mock
import org.mockito.kotlin.whenever

@OptIn(ExperimentalCoroutinesApi::class)
class GuideViewModelTest {
    private val testDispatcher = UnconfinedTestDispatcher()
    private lateinit var repository: GuideRepository
    private lateinit var viewModel: GuideViewModel

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)
        repository = mock()
        whenever(repository.articles()).thenReturn(flowOf(emptyList()))
        viewModel = GuideViewModel(repository)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `initial sync status is IDLE`() {
        assertEquals(SyncStatus.IDLE, viewModel.syncStatus.value)
        assertFalse(viewModel.isRefreshing.value)
    }

    @Test
    fun `successful sync updates status to SUCCESS then returns to IDLE after 3 seconds`() =
        runTest(testDispatcher) {
            whenever(repository.refresh()).thenReturn(Result.success(Unit))

            viewModel.refreshArticles()

            assertEquals(SyncStatus.SUCCESS, viewModel.syncStatus.value)
            assertFalse(viewModel.isRefreshing.value)

            advanceTimeBy(2_999)
            testScheduler.runCurrent()
            assertEquals(SyncStatus.SUCCESS, viewModel.syncStatus.value)

            advanceTimeBy(1)
            testScheduler.runCurrent()
            assertEquals(SyncStatus.IDLE, viewModel.syncStatus.value)
        }

    @Test
    fun `failed sync updates status to FAILURE then returns to IDLE after 3 seconds`() =
        runTest(testDispatcher) {
            whenever(repository.refresh()).thenReturn(Result.failure(RuntimeException("Network error")))

            viewModel.refreshArticles()

            assertEquals(SyncStatus.FAILURE, viewModel.syncStatus.value)
            assertFalse(viewModel.isRefreshing.value)

            advanceTimeBy(3_000)
            testScheduler.runCurrent()
            assertEquals(SyncStatus.IDLE, viewModel.syncStatus.value)
        }

    @Test
    fun `consecutive refresh cancels previous feedback timeout job`() =
        runTest(testDispatcher) {
            whenever(repository.refresh()).thenReturn(Result.failure(RuntimeException("fail")))

            viewModel.refreshArticles()
            assertEquals(SyncStatus.FAILURE, viewModel.syncStatus.value)

            advanceTimeBy(1_000)
            testScheduler.runCurrent()

            // Trigger second refresh which succeeds
            whenever(repository.refresh()).thenReturn(Result.success(Unit))
            viewModel.refreshArticles()
            assertEquals(SyncStatus.SUCCESS, viewModel.syncStatus.value)

            advanceTimeBy(2_500)
            testScheduler.runCurrent()
            assertEquals(SyncStatus.SUCCESS, viewModel.syncStatus.value)

            advanceTimeBy(500)
            testScheduler.runCurrent()
            assertEquals(SyncStatus.IDLE, viewModel.syncStatus.value)
        }

    @Test
    fun `category filter and search query updates correctly`() {
        viewModel.onCategoryFilter(GuideCategory.BALI)
        assertEquals(GuideCategory.BALI, viewModel.selectedCategory.value)

        viewModel.onSearchQueryChange("bali")
        assertEquals("bali", viewModel.searchQuery.value)
    }
}
