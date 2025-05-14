<?php
// routes/web.php
Route::get('/', function () {
    return redirect('/login');
});

Route::middleware(['auth'])->group(function () {
    Route::get('/dashboard', 'DashboardController@index')->name('dashboard');
});

Auth::routes();

// resources/views/auth/login.blade.php
@extends('layouts.app')

@section('content')
<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">{{ __('Login') }}</div>

                <div class="card-body">
                    <form method="POST" action="{{ route('login') }}">
                        @csrf
                        <div class="form-group row">
                            <label for="email">{{ __('E-Mail') }}</label>
                            <input id="email" type="email" class="form-control @error('email') is-invalid @enderror" 
                                   name="email" value="{{ old('email') }}" required>
                        </div>

                        <div class="form-group row">
                            <label for="password">{{ __('Senha') }}</label>
                            <input id="password" type="password" class="form-control @error('password') is-invalid @enderror" 
                                   name="password" required>
                        </div>

                        <div class="form-group row">
                            <button type="submit" class="btn btn-primary">
                                {{ __('Login') }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
@endsection

// app/Http/Controllers/DashboardController.php
<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Quitado;
use Carbon\Carbon;

class DashboardController extends Controller
{
    public function index()
    {
        $quitados = Quitado::where('SITUAÇÃO', 'QUITADO')->get();
        
        // Get counts by RESPONSAVEL
        $respCounts = $quitados->groupBy('RESPONSAVEL')
            ->map->count()
            ->sortDesc();
            
        // Get counts by date
        $dailyCounts = $quitados->groupBy(function($item) {
            return Carbon::parse($item->DATA)->format('d/m/Y');
        })->map->count()
        ->sortKeys();
        
        // Calculate totals
        $total = $quitados->count();
        $totalValue = $quitados->sum('VALOR_NUMERIC');
        
        return view('dashboard', compact(
            'respCounts',
            'dailyCounts',
            'total',
            'totalValue'
        ));
    }
}

// resources/views/dashboard.blade.php
@extends('layouts.app')

@section('content')
<div class="container-fluid">
    <div class="row">
        <!-- Sidebar -->
        <nav class="col-md-2 d-none d-md-block bg-light sidebar">
            <div class="sidebar-sticky">
                <ul class="nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link active" href="#">
                            Dashboard
                        </a>
                    </li>
                </ul>
            </div>
        </nav>

        <!-- Main Content -->
        <main class="col-md-10 ml-sm-auto">
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1>Dashboard Quitados</h1>
            </div>

            <!-- Summary Cards -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Total Quitados</h5>
                            <h2>{{ $total }}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Valor Total</h5>
                            <h2>R$ {{ number_format($totalValue, 2, ',', '.') }}</h2>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Charts -->
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Por Responsável</h5>
                            <canvas id="respChart"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Evolução Diária</h5>
                            <canvas id="dailyChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tables -->
            <div class="row mt-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Detalhamento</h5>
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Responsável</th>
                                        <th>Quantidade</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    @foreach($respCounts as $resp => $count)
                                    <tr>
                                        <td>{{ $resp }}</td>
                                        <td>{{ $count }}</td>
                                    </tr>
                                    @endforeach
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>
</div>

@push('scripts')
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    // Responsável Chart
    new Chart(document.getElementById('respChart'), {
        type: 'bar',
        data: {
            labels: {!! json_encode($respCounts->keys()) !!},
            datasets: [{
                label: 'Quantidade',
                data: {!! json_encode($respCounts->values()) !!}
            }]
        }
    });

    // Daily Chart
    new Chart(document.getElementById('dailyChart'), {
        type: 'line',
        data: {
            labels: {!! json_encode($dailyCounts->keys()) !!},
            datasets: [{
                label: 'Quantidade',
                data: {!! json_encode($dailyCounts->values()) !!}
            }]
        }
    });
</script>
@endpush
@endsection

// app/Models/Quitado.php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Quitado extends Model
{
    protected $table = 'quitados';
    
    protected $fillable = [
        'DATA',
        'CTT',
        'NOME',
        'VALOR',
        'RESPONSAVEL',
        'SITUAÇÃO',
        'BANCO'
    ];

    protected $dates = ['DATA'];
}

// database/migrations/2021_01_01_000000_create_quitados_table.php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class CreateQuitadosTable extends Migration
{
    public function up()
    {
        Schema::create('quitados', function (Blueprint $table) {
            $table->id();
            $table->date('DATA');
            $table->string('CTT');
            $table->string('NOME');
            $table->string('VALOR');
            $table->string('RESPONSAVEL');
            $table->string('SITUAÇÃO');
            $table->string('BANCO');
            $table->timestamps();
        });
    }

    public function down()
    {
        Schema::dropIfExists('quitados');
    }
}

// app/Console/Commands/ImportQuitados.php
<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\Quitado;
use Carbon\Carbon;

class ImportQuitados extends Command
{
    protected $signature = 'import:quitados';
    protected $description = 'Import quitados from CSV';

    public function handle()
    {
        $filepath = base_path('_DEMANDAS DE MARÇO_2025 - QUITADOS.csv');
        
        if (!file_exists($filepath)) {
            $this->error('CSV file not found!');
            return;
        }

        $this->info('Importing quitados...');
        
        $csv = array_map('str_getcsv', file($filepath));
        array_shift($csv); // Remove header
        
        foreach ($csv as $row) {
            Quitado::create([
                'DATA' => Carbon::createFromFormat('d/m/Y', $row[0]),
                'CTT' => $row[1],
                'NOME' => $row[3],
                'VALOR' => $row[4],
                'RESPONSAVEL' => $row[13],
                'SITUAÇÃO' => $row[14],
                'BANCO' => $row[12]
            ]);
        }

        $this->info('Import completed!');
    }
}