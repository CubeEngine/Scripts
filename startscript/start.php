#!/usr/bin/php
<?php

    define('DS',            DIRECTORY_SEPARATOR);
    define('BASE_DIR',      dirname(__FILE__) . DS);
    define('SERVER_DIR',    BASE_DIR . 'server' . DS);
    define('JAVA',          'java');
    define('RAM',           '256M');
    define('JAR_NAME',      'server.jar');

    function downloadServer($channel)
    {
        echo "Downloading the server ... ";
        if (@copy("http://dl.bukkit.org/downloads/craftbukkit/get/$channel/craftbukkit.jar", SERVER_DIR . JAR_NAME))
        {
            echo "done!\n";
        }
        else
        {
            echo "failed!\n";
        }
    }
    
    function setupFolders()
    {
        $server = BASE_DIR . 'server';
        if (!file_exists(SERVER_DIR))
        {
            echo "Creating server folder...";
            mkdir(SERVER_DIR, 0766);
            echo "done!\n";
        }
        else if(file_exists(SERVER_DIR) && !is_dir(SERVER_DIR))
        {
            echo SERVER_DIR . " exists, but it's not a folder!\n";
            exit(1);
        }
    }

    function copyFiles()
    {
        $files = @file(BASE_DIR . 'files.txt', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        if (is_array($files))
        {
            $slashes = array('/', '\\');
            foreach ($files as $file)
            {
                $file = trim($file);
                if ($file[0] == ';')
                {
                    continue;
                }
                list($source, $target) = explode('|', trim($file));
                $source = trim($source);
                
                foreach ($_SERVER as $key => $value)
                {
                    if (is_string($value))
                    {
                        $source = str_ireplace('%' . $key . '%', $value, $source);
                    }
                }

                if (substr_count($source, '*'))
                {
                    $result = glob($source);
                    if (is_array($result) && count($result) && is_file($result[0]))
                    {
                        $source = $result;
                    }
                    else
                    {
                        continue;
                    }
                }

                $target = SERVER_DIR . trim(str_replace($slashes, DS, trim($target)), DS);
                echo "Coping ... \n";
                if (!is_array($source) || (is_array($source) && count($source) === 1))
                {
                    if (is_array($source))
                    {
                        $source = $source[0];
                    }
                    echo "\tFrom: $source\n";
                    echo "\tTo:   $target\n";
                    echo "... ";
                    @mkdir(dirname($target), 0766, true);
                    if (!@rename($source, $target))
                    {
                        echo 'failed!';
                    }
                    else
                    {
                        echo 'done!';
                    }
                }
                else
                {
                    $target = rtrim($target, '/\\') . DS;
                    @mkdir($target, 0766, true);
                    echo "\tTo:   $target\n";

                    foreach ($source as $path)
                    {
                        echo "\tFrom: $path...";
                        if (!rename($path, $target . basename($path)))
                        {
                            echo 'failed!';
                        }
                        else
                        {
                            echo 'done!';
                        }
                        echo "\n";
                    }
                }
                echo "\n";
            }
        }
    }

    function cmd_debug()
    {
        cmd_run('-agentlib:jdwp=transport=dt_socket,address=localhost:9009,server=y,suspend=y');
    }
    
    function cmd_run($javaargs = '-agentlib:jdwp=transport=dt_socket,address=localhost:9009,server=y,suspend=n', $serverargs = '')
    {
        if (strlen($javaargs))
        {
            $javaargs = ' ' . $javaargs;
        }
        if (strlen($serverargs))
        {
            $serverargs = ' ' . $serverargs;
        }
        $jar = SERVER_DIR . JAR_NAME;
        if (!file_exists($jar))
        {
            cmd_update();
        }


        $pipes = array();
        $cmd = JAVA . ' -Xmx' . RAM . ' -Xms' . RAM . $javaargs . ' -jar "' . $jar . '"' . $serverargs;
        echo "Command: $cmd\n";
        echo `java -version`;
        while (true)
        {
            copyFiles();
            $proc = @proc_open($cmd, array(STDIN, STDOUT, STDERR), $pipes, SERVER_DIR, $_SERVER);
            proc_close($proc);
        }
    }
    
    function cmd_copy()
    {
        copyFiles();
    }
    
    function cmd_update($slug = 'latest-rb')
    {
        downloadServer($slug);
    }

    function cmd_update_dev()
    {
        cmd_update('latest');
    }

    setupFolders();
    $command = 'run';
    $args = array();
    
    if ($argc > 1)
    {
        $cmd = trim($argv[1]);
        if (strlen($cmd))
        {
            $command = $argv[1];
            $args = array_slice($argv, 2);
        }
    }

    try
    {
        $function = new ReflectionFunction('cmd_' . $command);
        $requiredParams = 0;
        foreach ($function->getParameters() as $param)
        {
            if (!$param->isOptional())
            {
                $requiredParams++;
            }
        }
        if (count($args) < $requiredParams)
        {
            echo "Not enough parameters specified, $requiredParams " . (abs($requiredParams) !== 1 ? 'are' : 'is') . " required!\n";
            exit(1);
        }
        $function->invokeArgs($args);
    }
    catch (ReflectionException $e)
    {
        echo "Command $command not found!\n";
        exit(1);
    }
?>
