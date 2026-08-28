<script lang="ts">
  import { CalendarDate, getLocalTimeZone, parseDate, today } from '@internationalized/date';
  import { CalendarDays, ChevronLeft, ChevronRight, X } from 'lucide-svelte';
  import { DateRangePicker, type DateRange } from 'bits-ui';

  export let label = 'Rentang tanggal';
  export let start = '';
  export let end = '';
  export let onChange: (range: { start: string; end: string }) => void = () => {};

  let range: DateRange = makeRange(start, end);
  let syncedStart = start;
  let syncedEnd = end;

  function makeRange(startDate: string, endDate: string): DateRange {
    return {
      start: startDate ? parseDate(startDate) : undefined,
      end: endDate ? parseDate(endDate) : undefined
    };
  }

  function formatDate(value: string) {
    return new Intl.DateTimeFormat('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }).format(parseDate(value).toDate(getLocalTimeZone()));
  }

  function displayValue() {
    if (!range.start || !range.end) return 'Semua tanggal';
    return `${formatDate(range.start.toString())} – ${formatDate(range.end.toString())}`;
  }

  function getRange() {
    return range;
  }

  function setRange(next: DateRange) {
    range = next;
    if (next.start && next.end) {
      onChange({ start: next.start.toString(), end: next.end.toString() });
    }
  }

  function clearRange(event: MouseEvent) {
    event.stopPropagation();
    range = makeRange('', '');
    onChange({ start: '', end: '' });
  }

  $: if (start !== syncedStart || end !== syncedEnd) {
    syncedStart = start;
    syncedEnd = end;
    range = makeRange(start, end);
  }
</script>

<div class="grid gap-1.5 text-xs font-bold text-[#52635b]">
  <span>{label}</span>
  <DateRangePicker.Root bind:value={getRange, setRange} placeholder={today(getLocalTimeZone()) as CalendarDate} locale="id-ID" weekStartsOn={1} weekdayFormat="short" numberOfMonths={1}>
    <div class="relative">
      <DateRangePicker.Trigger class="flex min-h-10 w-full items-center justify-between gap-2 rounded-lg border border-[#cfdad4] bg-white px-3 py-2 pr-10 text-left text-sm font-normal text-[#17241f] transition hover:border-[#aebfb6] focus-visible:border-[#4d8a6c] focus-visible:ring-4 focus-visible:ring-[#18794e]/10">
        <span class="flex min-w-0 items-center gap-2 truncate"><CalendarDays size={16} strokeWidth={1.8} class="shrink-0 text-[#718078]" aria-hidden="true" />{displayValue()}</span>
      </DateRangePicker.Trigger>
      {#if range.start && range.end}<button class="absolute right-2 top-1/2 grid size-6 min-h-0 -translate-y-1/2 place-items-center rounded-md bg-transparent p-0 text-[#718078] hover:bg-[#edf5f1] hover:text-[#176b49]" type="button" aria-label="Hapus rentang tanggal" onclick={clearRange}><X size={14} aria-hidden="true" /></button>{/if}
    </div>
    <DateRangePicker.Content class="z-50 mt-2 rounded-xl border border-[#d5e1db] bg-white p-4 text-[#17241f] shadow-[0_14px_30px_rgba(23,36,31,.14)]" align="start">
      <DateRangePicker.Calendar>
        {#snippet children({ months, weekdays })}
          <DateRangePicker.Header class="mb-3 flex items-center justify-between gap-3">
            <DateRangePicker.PrevButton class="grid size-8 min-h-0 place-items-center rounded-md bg-transparent p-0 text-[#53645b] hover:bg-[#edf5f1] hover:text-[#176b49]"><ChevronLeft size={16} aria-hidden="true" /></DateRangePicker.PrevButton>
            <DateRangePicker.Heading class="text-sm font-bold" />
            <DateRangePicker.NextButton class="grid size-8 min-h-0 place-items-center rounded-md bg-transparent p-0 text-[#53645b] hover:bg-[#edf5f1] hover:text-[#176b49]"><ChevronRight size={16} aria-hidden="true" /></DateRangePicker.NextButton>
          </DateRangePicker.Header>
          {#each months as month}
            <DateRangePicker.Grid class="border-collapse">
              <DateRangePicker.GridHead>
                <DateRangePicker.GridRow>
                  {#each weekdays as weekday}
                    <DateRangePicker.HeadCell class="size-8 text-center text-[.65rem] font-bold uppercase text-[#718078]">{weekday}</DateRangePicker.HeadCell>
                  {/each}
                </DateRangePicker.GridRow>
              </DateRangePicker.GridHead>
              <DateRangePicker.GridBody>
                {#each month.weeks as weekDates}
                  <DateRangePicker.GridRow>
                    {#each weekDates as date}
                      <DateRangePicker.Cell {date} month={month.value}>
                        <DateRangePicker.Day class="grid size-8 place-items-center rounded-md text-xs text-[#40554a] outline-none hover:bg-[#edf5f1] data-[selected]:bg-[#176b49] data-[selected]:font-bold data-[selected]:text-white data-[outside-month]:text-[#b5c1ba] data-[highlighted]:bg-[#dceee5]">{date.day}</DateRangePicker.Day>
                      </DateRangePicker.Cell>
                    {/each}
                  </DateRangePicker.GridRow>
                {/each}
              </DateRangePicker.GridBody>
            </DateRangePicker.Grid>
          {/each}
        {/snippet}
      </DateRangePicker.Calendar>
    </DateRangePicker.Content>
  </DateRangePicker.Root>
</div>
