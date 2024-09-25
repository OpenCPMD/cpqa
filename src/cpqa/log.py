# CPQA is a Quality Assurance framework for CP2K.
# Copyright (C) 2010 Toon Verstraelen <Toon.Verstraelen@UGent.be>.
#
# This file is part of CPQA.
#
# CPQA is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# CPQA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --


import os, difflib


__all__ = ['log_txt', 'log_html', 'diff_txt', 'diff_html']


def log_txt(runner, timer, f=None):
    config = runner.config
    if f is None:
        f = open(os.path.join(config.tstdir, 'cpqa.log'), 'w')
        print('... Writing text log:', f.name)
        do_close = True
    else:
        do_close = False

    print('Total wall time [s]: %.2f' % timer.seconds, file=f)
    print('Disk usage in ref-... [Mb]: %.2f' % (runner.refsize/1048576.0), file=f)
    print('Disk usage in tst-... [Mb]: %.2f' % (runner.tstsize/1048576.0), file=f)

    # Extended overview
    for test_input in runner.test_inputs:
        result = test_input.tst_result
        if result is None:
            continue
        if not result.flags['ok']:
            print('~'*80, file=f)
            print('Problems with %s' % test_input.path_inp, file=f)
            if result.flags['error']:
                print(' * Something went wrong in the CPQA driver script.', file=f)
                counter = 0
                for message in result.messages:
                    for line in message.split('\n'):
                        print('    %03i|%s' % (counter, line), file=f)
                    counter += 1
            if result.flags['different'] or result.flags['wrong']:
                print(' * Some values are wrong and/or different compared to the reference.', file=f)
                for test in result.tests:
                    if test.wrong or test.different:
                        print('    %s' % test.get_command(), file=f)
                        print('    !!!', end=' ', file=f)
                        if test.wrong:
                            print('WRONG', end=' ', file=f)
                        if test.different:
                            print('DIFFERENT', end=' ', file=f)
                        print('!!!', file=f)
                        test.log_txt(f)
            if result.flags['missing']:
                print(' * Some values in the output could not be found', file=f)
                for test in result.tests:
                    if not test.complete(result.flags['new']):
                        print('    %s' % test.get_command(), file=f)
            if result.flags['failed']:
                print(' * Test run gave a non-zero return code.', file=f)
                print('   ----- last 20 lines of output -----', file=f)
                for line in result.last_out_lines:
                    print(line, file=f)
            if result.flags['verbose']:
                print(' * Test run gave some standard error.', file=f)
                print('   ----- last 20 lines of standard error -----', file=f)
                for line in result.last_stderr_lines:
                    print(line, file=f)
            if result.flags['leak']:
                print(' * Some memory leaks were detect. Check the stderr.', file=f)
            print('~'*80, file=f)

    # Short summary
    counters = {}
    for test_input in runner.test_inputs:
        result = test_input.tst_result
        if result is None:
            continue
        for key in result.flags:
            counters[key] = result.flags[key] + counters.get(key, 0)
    print('='*80, file=f)
    for key, value in sorted(counters.items()):
        if value > 0:
            value_str = '%5i' % value
        else:
            value_str = '    -'
        print(' %1s %10s %5s' % (key[0].upper(), key.upper(), value_str), file=f)
    print('   %10s %5i' % ('TOTAL', len(runner.test_inputs)), file=f)
    print('='*80, file=f)

    if do_close:
        f.close()

css = """
body { font-family: sans; font-size: 10pt; }
td { border: solid 1px #666; text-align: right; padding: 3px 3px; white-space: nowrap; }
th { border: solid 1px #666; text-align: right; padding: 3px 3px; white-space: nowrap; }
table { border-collapse: collapse; border: solid 1px black; font-size: 10pt; }
p.cat { color: #800; }
.grey { background-color: #AAA; }
.green { background-color: #AFA; }
.red { background-color: #FAA; }
.purple { background-color: #FAF; }
//tr { border: solid 1px #666; }
"""

def log_html(runner, timer):
    config = runner.config
    f = open(os.path.join(config.tstdir, 'index.html'), 'w')
    print('... Writing html log:', f.name)
    print('<html><head>', file=f)
    print('<title>CPQA log</title>', file=f)
    print('<style type="text/css">%s</style>' % css, file=f)
    print('</head><body>', file=f)
    print('<h1>CPQA log</h1>', file=f)

    print('<h2>General info</h2>', file=f)
    print('<table>', file=f)
    print('<tr><th>Root</th><td>%s</td></tr>' % config.root, file=f)
    print('<tr><th>Arch</th><td>%s</td></tr>' % config.arch, file=f)
    print('<tr><th>Version</th><td>%s</td></tr>' % config.version, file=f)
    print('<tr><th>NProc</th><td>%i</td></tr>' % config.nproc, file=f)
    if config.mpi_prefix is not None:
        print('<tr><th>NProc MPI</th><td>%i</td></tr>' % config.nproc_mpi, file=f)
        print('<tr><th>MPI prefix</th><td>%s</td></tr>' % config.mpi_prefix, file=f)
    if config.mpi_suffix is not None:
        print('<tr><th>MPI suffix</th><td>%s</td></tr>' % config.mpi_suffix, file=f)
    print('<tr><th>Reference directory</th><td>%s</td></tr>' % config.refdir, file=f)
    print('<tr><th>Test directory</th><td>%s</td></tr>' % config.tstdir, file=f)
    for select_dir in config.select_dirs:
        print('<tr><th>Select dir</th><td>%s</td></tr>' % select_dir, file=f)
    for select_path_inp in config.select_paths_inp:
        print('<tr><th>Select path inp</th><td>%s</td></tr>' % select_path_inp, file=f)
    if config.faster_than is not None:
        print('<tr><th>Faster than</th><td>%.2fs</td></tr>' % config.faster_than, file=f)
    if config.slower_than is not None:
        print('<tr><th>Slower than</th><td>%.2fs</td></tr>' % config.slower_than, file=f)
    print('<tr><th>Number of test jobs</th><td>%i</td></tr>' % len(runner.test_inputs), file=f)
    print('<tr><th>Total wall time [s]</th><td>%.2f</td></tr>' % timer.seconds, file=f)
    print('</table>', file=f)

    print('<h2>Summary</h2>', file=f)
    print('<table>', file=f)
    print('<tr><th>Flag</th><th>Label</th><th>Count</th></tr>', file=f)
    counters = {}
    for test_input in runner.test_inputs:
        result = test_input.tst_result
        if result is None:
            continue
        for key in result.flags:
            counters[key] = result.flags[key] + counters.get(key, 0)
    for key, value in sorted(counters.items()):
        if value > 0:
            value_str = '%i' % value
        else:
            value_str = '-'
        print('<tr><td>%1s</td><td>%10s</td><td>%s</td></tr>' % (key[0].upper(), key.upper(), value_str), file=f)
    print('<tr><td>&nbsp;</td><td>%10s</td><td>%i</td></tr>' % ('TOTAL', len(runner.test_inputs)), file=f)
    print('</table>', file=f)

    print('<h2>Regressions</h2>', file=f)
    for test_input in runner.test_inputs:
        result = test_input.tst_result
        if result is None:
            continue
        if not result.flags['ok']:
            print('<h3>%s</h3>' % test_input.path_inp, file=f)
            print('<p><a href=\'%s\'>%s</a></p>' % (test_input.path_out, test_input.path_out), file=f)
            if result.flags['error']:
                print('<p class="cat">Something went wrong in the CPQA driver script.</p>', file=f)
                print('<ol>', file=f)
                for message in result.messages:
                    print('<li><pre>%s</pre></li>' % message, file=f)
                print('</ol>', file=f)
            if result.flags['wrong'] or result.flags['different']:
                print('<p class="cat">Some values are wrong and/or different compared to the reference.</p>', file=f)
                if result.flags['different']:
                    fn_html_diff = diff_html_file(config, test_input)
                    print('<p>Full diff: <a href="%s">%s</a>' % (fn_html_diff, fn_html_diff), file=f)
                print('<ol>', file=f)
                for test in result.tests:
                    if test.wrong or test.different:
                        print('<li><pre>%s</pre>' % test.get_command(), end=' ', file=f)
                        if test.wrong:
                            print('<b>WRONG</b>', end=' ', file=f)
                        if test.different:
                            print('<b>DIFFERENT</b>', end=' ', file=f)
                        print('<br /><pre>', file=f)
                        test.log_html(f)
                        print('</pre></li>', file=f)
                print('</ol>', file=f)
            if result.flags['missing']:
                print('<p class="cat">Some values in the output could not be found.</p>', file=f)
                print('<ol>', file=f)
                for test in result.tests:
                    if not test.complete(result.flags['new']):
                        print('<li><pre>%s</pre></li>' % test.get_command(), file=f)
                print('</ol>', file=f)
            if result.flags['failed']:
                print('<p class="cat">Test run gave a non-zero return code.</p>', file=f)
                print('<p>Last 20 lines of output:</p>', file=f)
                print('<pre class="grey">', file=f)
                for line in result.last_out_lines:
                    print(line, file=f)
                print('</pre>', file=f)
            if result.flags['verbose']:
                print('<p class="cat">Test run gave some standard error.</p>', file=f)
                print('<p>Last 20 lines of standard error:</p>', file=f)
                print('<pre class="grey">', file=f)
                for line in result.last_stderr_lines:
                    print(line, file=f)
                print('</pre>', file=f)
            if result.flags['leak']:
                print('<p class="cat">Some memory leaks were detect. Check the stderr.</p>', file=f)

    print('</body></html>', file=f)
    f.close()


def diff_txt(f, old, new, oldname, newname, indent=''):
    red = "\033[0;31m"
    green = "\033[0;32m"
    reset = "\033[m"
    print(indent + ('Diff from %s to %s:' % (oldname, newname)), file=f)
    for line in difflib.ndiff(old, new):
        if line.startswith('+'):
            if f.isatty():
                print(green + line[:-1] + reset, file=f)
            else:
                print(line[:-1], file=f)
        elif line.startswith('-'):
            if f.isatty():
                print(red + line[:-1] + reset, file=f)
            else:
                print(line[:-1], file=f)

def diff_html(f, old, new, oldname, newname):
    print('<pre>', file=f)
    for line in difflib.unified_diff(old, new, oldname, newname):
        line = line[:-1]
        if line.startswith('---'):
            open_tag = '<b class="red">'
            close_tag = '</b>'
        elif line.startswith('+++'):
            open_tag = '<b class="green">'
            close_tag = '</b>'
        elif line.startswith('-'):
            open_tag = '<span class="red">'
            close_tag = '</span>'
        elif line.startswith('+'):
            open_tag = '<span class="green">'
            close_tag = '</span>'
        elif line.startswith('@@') and line.endswith('@@'):
            open_tag = '<i class="purple">'
            close_tag = '</i>'
        else:
            open_tag = ''
            close_tag = ''
        print(open_tag + line + close_tag, file=f)
    print('</pre>', file=f)


def diff_html_file(config, test_input):
    f_ref = open(os.path.join(config.refdir, test_input.path_out))
    ref_lines = f_ref.readlines()
    f_ref.close()
    f_tst = open(os.path.join(config.tstdir, test_input.path_out))
    tst_lines = f_tst.readlines()
    f_tst.close()

    f_html = open(os.path.join(config.tstdir, test_input.path_out + '.diff.html'), 'w')
    print('... Writing html log:', f_html.name)
    print('<html><head>', file=f_html)
    print('<title>Diff for %s</title>' % test_input.path_out, file=f_html)
    print('<style type="text/css">%s</style>' % css, file=f_html)
    print('</head><body>', file=f_html)
    print('<h2>Diff for %s</h2>' % test_input.path_out, file=f_html)
    diff_html(f_html, ref_lines, tst_lines, 'ref', 'tst')
    print('</body></html>', file=f_html)
    f_html.close()

    return test_input.path_out + '.diff.html'
